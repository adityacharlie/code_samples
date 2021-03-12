import React, { PureComponent } from 'react'
import './NewsFeedScreen.css'
import { withRouter } from 'react-router-dom'
import { getTrans } from '../../utils'
import BaseScreen from '../BaseScreen/BaseScreen'
import NewsCard from '../../components/NewsFeedCard/NewsCard'
import axios from 'axios'
import InfiniteScroll from 'react-infinite-scroller'
import Loader from 'react-loader-spinner'

class NewsFeedScreen extends PureComponent {
    state = {
        rawNews: [],
        groupName: '',
        isLoading: false,
        hasMoreItems: true,
    }

    componentDidMount() {
        this.getRawNews()
    }

    componentDidUpdate(prevProps) {
        const { match } = this.props

        if (match.params.id !== prevProps.match.params.id) {
            this.setState({ hasMoreItems: true })
            this.getRawNews()
        }
    }

    async getRawNews() {
        const { match } = this.props

        this.setState({ isLoading: true })

        await axios
            .get(`/news/raw-news/group/${match.params.id}/`)
            .then(response => {
                // console.log('news feed response', response.data)
                this.setState({
                    rawNews: response.data.results.data,
                    groupName: response.data.results.group_name,
                    next: response.data.next,
                    previous: response.data.previous,
                    hasMoreItems: !!response.data.next,
                })
            })

        this.setState({ isLoading: false })
    }

    handleLoadMore = async page => {
        if (this.state.next && !this.state.isLoading) {
            this.setState({ isLoading: true })

            await axios.get(this.state.next).then(response => {
                console.log('load more feeds response', response.data)
                this.setState(prevState => {
                    return {
                        rawNews: [
                            ...prevState.rawNews,
                            ...response.data.results.data,
                        ],
                        next: response.data.next,
                        previous: response.data.previous,
                        hasMoreItems: !!response.data.next,
                    }
                })
            })

            this.setState({ isLoading: false })
        }
    }

    removeFeedCard = id => {
        this.setState(prevState => ({
            rawNews: prevState.rawNews.filter(item => item.id !== id),
        }))
    }

    render() {
        return (
            <BaseScreen>
                <div className="newsfeed-main-title">
                    <h1 className="title-1">
                        {`${getTrans('News Feed for ')} ${
                            this.state.groupName
                        }`}
                    </h1>
                </div>
                <div className="newsfeed-card-list">
                    <InfiniteScroll
                        pageStart={0}
                        loadMore={this.handleLoadMore}
                        hasMore={this.state.hasMoreItems}
                        loader={
                            <Loader
                                key={0}
                                type="Grid"
                                color="#adadad"
                                height={80}
                                width={80}
                            />
                        }
                    >
                        {this.state.rawNews.map(item => (
                            <NewsCard
                                key={item.id}
                                {...item}
                                removeFeedCard={this.removeFeedCard}
                            />
                        ))}
                    </InfiniteScroll>
                </div>
            </BaseScreen>
        )
    }
}

export default withRouter(NewsFeedScreen)
