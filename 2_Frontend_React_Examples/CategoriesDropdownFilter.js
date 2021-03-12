import React, { useState, useEffect } from 'react'
import blueCheck from '../../assets/icons/blue-checkmark.svg'
import emptyCheck from '../../assets/icons/empty-checkmark.svg'

export default function CategoriesDropdownFilter(props) {
    const [expanded, setexpanded] = useState(false)
    const [selectedSubCategories, SetSelectedSubCategories] = useState([])

    useEffect(() => {
        let arrTemp = []
        props.selectedCategories.forEach(cat => {
            cat.subcategories.forEach(sub => {
                arrTemp.push(sub.id)
            })
        })
        SetSelectedSubCategories(arrTemp)
    }, [props.selectedCategories])

    const selectablesMap = props.allCategories.map(cat => {
        return (
            <div key={cat.id}>
                <div
                    className="multiSelectDropDown__option"
                    onClick={() => props.handleCategoryFilterChange('cat', cat.name, cat.id, null, null)}
                >
                    <img
                        src={props.selectedCategories.find(arr => arr.name === cat.name) ? blueCheck : emptyCheck}
                        alt="checkbox"
                    />
                    <p>{cat.name}</p>
                </div>
                <div>
                    {cat.subcategories.map(sub => {
                        return (
                            <div
                                className="multiSelectDropDown__subCat"
                                key={sub.name}
                                onClick={() =>
                                    props.handleCategoryFilterChange('sub', cat.name, cat.id, sub.name, sub.id)
                                }
                            >
                                <img
                                    src={selectedSubCategories.find(arr => arr === sub.id) ? blueCheck : emptyCheck}
                                    alt="checkbox"
                                />
                                <p>{sub.name}</p>
                            </div>
                        )
                    })}
                </div>
            </div>
        )
    })

    return (
        <div style={dropdownStyle}>
            <div onClick={() => (expanded ? setexpanded(false) : setexpanded(true))}>
                <p style={headingStyle}>Categories/Sub</p>
            </div>

            {expanded && (
                <div className="multiSelectDropDown__dropdownExpandedBox" style={expandedStyle}>
                    {selectablesMap}
                </div>
            )}
        </div>
    )
}

const dropdownStyle = {
    width: '200px',
    height: '38px',
    paddingLeft: '20px',
    borderRadius: '3px',
    marginRight: '10px',
    border: '1px solid rgb(169, 169, 169)',
    backgroundColor: 'white',
    cursor: 'pointer',
}
const headingStyle = {
    marginTop: '6px',
}
const expandedStyle = {
    height: '350px',
    overflowY: 'scroll',
}
