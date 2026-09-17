import React from 'react';

interface FormValidity {
    validity : Record<string, boolean>,
    setValidity : (valid : string, isValid : boolean) => void
}

export const Validity = React.createContext<FormValidity>({validity:{}, setValidity : (inputLabel : string, isValid: boolean) => {}})