# AN EXAMPLE OF A REDIS CACHE I IMPLEMENTED
# THIS FUNCTION (rmcache) WAS BEING USED AS ROUTE IN A BOTTLE FRAMEWORK APPLICATION

import json
import cache
import settings
import MySQLdb
import MySQLdb.cursors
import logging
import redis
import datetime


today = datetime.date.today().strftime("%Y%m%d")

memory = cache.Client()
memory.set('cache_empty', True)

redis_instance = redis.Redis(host=settings.REDIS_SERVER_NODE,
                             port=settings.REDIS_PORT)


def return_db_attrs():
    conn = MySQLdb.connect(user=settings.DATABASE['USER'],
                           passwd=settings.DATABASE['PASSWORD'],
                           db=settings.DATABASE['NAME'],
                           host=settings.DATABASE['HOST'],
                           cursorclass=MySQLdb.cursors.DictCursor)
    db = conn.cursor()
    return conn, db


def rmcache():
    conn, db = return_db_attrs()

    # Promotions Cache
    # Start and end targeting
    db.execute("""SELECT * FROM ads_promotion WHERE disabled <> 1
        and ((start IS NULL and end IS NULL) or {0} BETWEEN start
        and end) """.format(today))
    promotions = db.fetchall()
    cache_promotions = {}
    promotion_ids = set()
    promotion_zset_keys = []
    for promotion in promotions:
        try:
            promotion["json"] = json.loads(promotion["json"])
        except ValueError:
            logging.warn("Corrupt JSON for Promotion "
                         "({0}): {1}".format(
                             promotion["id"], promotion["name"]))
            continue
        cache_promotions["p_{0}".format(promotion["id"])] = promotion
        promotion_ids.add(promotion["id"])
        # ZUNIONSET ALl
        promotion_zset_keys.extend([int(promotion['id']), 0])
        redis_instance.zadd('sr:pr:all', *promotion_zset_keys)

    # Total Impressions targeting
    db.execute("""SELECT sum(impressions) as impressions, prid FROM """
               """reports_ads WHERE prid IN ({0}) and """
               """year(server_date)=%s GROUP BY prid""".format(
                   ",".join(map(str, promotion_ids))),
               (today[:4],))
    db_traffic = db.fetchall()
    for record in db_traffic:
        cache_promotion = cache_promotions["p_{0}".format(record['prid'])]
        if cache_promotion['tcap'] != 0 and record['impressions'] > cache_promotion['tcap']:
            cache_promotions.pop("p_{0}".format(record['prid']), None)

    # Today Impressions targeting
    db.execute("""SELECT sum(impressions) as impressions, prid FROM """
               """reports_ads WHERE prid IN ({0}) and server_date=%s """
               """GROUP BY prid""".format(",".join(map(str, promotion_ids))),
               (today, ))
    db_traffic = db.fetchall()
    for record in db_traffic:
        cache_promotion = cache_promotions["p_{0}".format(record['prid'])]
        if cache_promotion['dcap'] != 0 and record['impressions'] > cache_promotion['dcap']:
            cache_promotions.pop("p_{0}".format(record['prid']), None)

    memory.set_multi(cache_promotions)

    memory.set("max_prid", max(promotion_ids))

    # Zones Cache
    db.execute("""SELECT * FROM ads_zone WHERE disabled <> 1""")
    zones = db.fetchall()
    cache_zones = {}
    zone_ids = set()
    for zone in zones:
        try:
            zone["json"] = json.loads(zone["json"])
        except ValueError:
            logging.warn("Corrupt JSON for Zone "
                         "({0}): {1}".format(zone["id"], zone["name"]))
            continue
        cache_zones["z_{0}".format(zone["id"])] = zone
        zone_ids.add(zone["id"])
    memory.set_multi(cache_zones)

    # Media Cache
    db.execute("""SELECT * FROM ads_media""")
    cache_media = {}
    medias = db.fetchall()
    for media in medias:
        cache_media["m_{0}".format(media["id"])] = media
    memory.set_multi(cache_media)

    # Segments Cache
    db.execute("""SELECT * FROM audience_segment ORDER BY id""")
    segments = db.fetchall()
    cache_segments = []
    for segment in segments:
        cache_segments.append(segment)
    memory.set("segment_cache", cache_segments)

    # Backup tags in cache
    mappings_file = "mappings.json"
    try:
        urls = []
        mappings_file = open(mappings_file)
        mappings_dict = json.load(mappings_file)
        memory.set_multi(mappings_dict)
    except IOError:
        print 'Could not open url blocklist file for reading: %s' % mappings_file
    except Exception:
        print 'Unknown Json format for DC backup mappings'

    # Url Blocklist
    filename = "blocked_urls.txt"
    try:
        urls = []
        with open(filename, 'r') as urls_file:
            urls = [lfile.strip() for lfile in urls_file if lfile.strip()]
        memory.set("url_block_list", urls)
    except IOError:
        print 'Could not open url blocklist file for reading: %s' % filename

    # Update Zone Promotion Map
    global ZONE_PROMOTION_MAP
    memory.set("z_p_map", ZONE_PROMOTION_MAP)

    db.close()
    conn.close()
