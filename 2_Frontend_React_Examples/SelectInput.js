import React, { PureComponent } from 'react'
import { FormGroup, Label } from 'reactstrap'
import classnames from 'classnames'
import { ErrorMessage } from 'formik'
import Select from 'react-select'


class MySelect extends PureComponent {

    handleChange = value => {
      // this is going to call setFieldValue and manually update values.topics
      this.props.onChange('topics', value);
    };

    handleBlur = () => {
      // this is going to call setFieldTouched and manually update touched.topcis
      this.props.onBlur('topics', true);
    };

    render() {

        const {
            name,
            label,
            placeholder,
            type,
            values,
            handleChange,
            handleBlur,
            errors,
            touched,
        } = this.props


        return (
            <FormGroup key={name}>
                <Label htmlFor={name}>{label}</Label>
                <Select
                id={name}
                placeholder={placeholder}
                options={options}
                multi={true}
                onChange={handleChange}
                onBlur={handleBlur}
                value={this.props.value}
                />

                <ErrorMessage
                    component={() => (
                        <div className="input-feedback">{errors[name]}</div>
                    )}
                    name={name}
                />
            </FormGroup>
        );
    }

}

export default MySelect