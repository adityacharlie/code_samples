import React, { PureComponent } from 'react'
import './AddEditUser.css'
import { Button, FormGroup, Label } from 'reactstrap'
import { Formik, Form, Field, ErrorMessage } from 'formik'
import { getTrans } from 'utils'
import withModal from 'hoc/withModal'
import axios from 'axios'
import { toast } from 'react-toastify'
import Select from 'react-select'

class AddEditUser extends PureComponent {
    state = {
        subscribedcompanies: this.props.subscribedcompanies,
        ExistingPackageCompanies: [],
    }

    componentDidMount() {
        this.getCompaniesSelectedPackages([])
    }

    handleChange = company => {
        this.setState({ subscribedcompanies: company })
    }

    async getCompaniesSelectedPackages(raw_packages) {
        // on select of packages update the existing_package_companies state to the multiple
        // companies of selected packages
        const params = {
            // Sending selected package list as params
            selected_packages: Array.from(raw_packages).map(option => option.value),
        }

        this.setState({ isLoading: true })

        axios
            .get(`/clientadmin/subscribed-companies/`, { params })
            .then(response => {
                this.state.ExistingPackageCompanies = response.data[0].companies
            })
            .finally(() => {
                this.setState({ isLoading: false })
            })
    }

    onSubmit = (values, { setSubmitting }) => {
        const { id, updateUser } = this.props

        setSubmitting(false)

        let companyIds = []

        if (this.state.subscribedcompanies && this.state.subscribedcompanies.length) {
            companyIds = this.state.subscribedcompanies.map(company => company.value)
        }

        const userData = {
            ...values,
            level: values.level ? values.level : null,
            practice_area: values.practice_area ? values.practice_area : null,
            companies: companyIds,
        }

        axios.patch(`/clientadmin/end-user/${id}/`, userData).then(response => {
            console.log('update user response', response)
            this.props.toggleModal()
            toast(getTrans('User updated'))
            updateUser(response.data)
        })
    }

    render() {
        const {
            toggleModal,
            practiceAreaList,
            levelList,
            subscribedPackages,
            packages = [],
            practice_area = {},
            email,
            first_name,
            last_name,
            office_phone,
            level,
        } = this.props

        return (
            <Formik
                initialValues={{
                    first_name,
                    last_name,
                    email,
                    practice_area: practice_area.id,
                    level: level.value,
                    office_phone,
                    packages: packages.map(item => item.id),
                    companies: this.state.ExistingPackageCompanies.map(item => item.id),
                }}
                onSubmit={this.onSubmit}
            >
                {({ isSubmitting, setFieldValue }) => (
                    <Form className="add-user-form">
                        <div className="add-user-form-container row">
                            <div className="col-lg-6 col-xl-6">
                                <FormGroup>
                                    <Label for="first_name">{getTrans('First Name')}</Label>
                                    <Field
                                        type="text"
                                        name={`first_name`}
                                        id="first_name"
                                        placeholder={getTrans('First Name')}
                                        className="form-control"
                                    />
                                </FormGroup>
                                <FormGroup>
                                    <Label for="last_name">{getTrans('Last Name')}</Label>
                                    <Field
                                        className="form-control"
                                        type="text"
                                        name={`last_name`}
                                        id="last_name"
                                        placeholder={getTrans('Last Name')}
                                    />
                                </FormGroup>
                                <FormGroup>
                                    <Label for="email">{getTrans('Email Address')}</Label>
                                    <Field
                                        className="form-control"
                                        type="email"
                                        name={`email`}
                                        id="email"
                                        placeholder="name@domain.com"
                                    />
                                    <ErrorMessage
                                        name="email"
                                        render={msg => <div className="input-feedback">{msg}</div>}
                                    />
                                </FormGroup>
                                <FormGroup>
                                    <Label>{getTrans('Practice Area')}</Label>
                                    <Field className="form-control" component="select" name="practice_area">
                                        <option value="">{getTrans('Select Area')}</option>
                                        {practiceAreaList.map(area => (
                                            <option key={area.id} value={area.id}>
                                                {area.name}
                                            </option>
                                        ))}
                                    </Field>
                                </FormGroup>
                                <FormGroup>
                                    <Label>{getTrans('Level')}</Label>
                                    <Field className="form-control" component="select" name="level">
                                        <option value="">{getTrans('Select Level')}</option>
                                        {levelList.map(level => (
                                            <option key={level.value} value={level.value}>
                                                {level.label}
                                            </option>
                                        ))}
                                    </Field>
                                </FormGroup>

                                <FormGroup>
                                    <Label for="office_phone">{getTrans('Office Phone Number')}</Label>
                                    <Field
                                        className="form-control"
                                        type="text"
                                        name={`office_phone`}
                                        id="office_phone"
                                        placeholder="ex. 514-555-5555"
                                    />
                                </FormGroup>
                                <FormGroup>
                                    <Label>{getTrans('Select packages')}</Label>
                                    <Field
                                        className="form-control"
                                        component="select"
                                        name="packages"
                                        multiple
                                        onChange={evt => {
                                            this.getCompaniesSelectedPackages(evt.target.selectedOptions)
                                            setFieldValue(
                                                'packages',
                                                [].slice.call(evt.target.selectedOptions).map(option => option.value)
                                            )
                                        }}
                                    >
                                        {subscribedPackages.map(packageItem => (
                                            <option key={packageItem.id} value={packageItem.id}>
                                                {packageItem.title}
                                            </option>
                                        ))}
                                    </Field>
                                </FormGroup>
                            </div>

                            <div className="col-lg-6 col-xl-6">
                                <FormGroup>
                                    <Label>{getTrans('Companies')}</Label>
                                    <Select
                                        isMulti
                                        name="companies"
                                        options={this.state.ExistingPackageCompanies}
                                        className="basic-multi-select"
                                        classNamePrefix="select"
                                        onChange={this.handleChange}
                                        value={this.state.subscribedcompanies}
                                    />
                                </FormGroup>
                            </div>
                        </div>
                        <div className="add-edit-custom-modal-buttons">
                            <Button color="primary" outline onClick={toggleModal} type="button">
                                {getTrans('Cancel')}
                            </Button>
                            <Button color="primary" type="submit" disabled={isSubmitting}>
                                {getTrans('Save')}
                            </Button>
                        </div>
                    </Form>
                )}
            </Formik>
        )
    }
}

export default withModal(AddEditUser)
