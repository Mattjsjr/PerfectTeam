"use client"
import { useEffect, useState } from "react";
import { OnChange } from "../types/stats";
import {schema} from '../types/zod'
import { useContext } from "react";
import { Validity } from "../context/FormValidityContext";

function FieldEntry({ label, onSelect } : { label: string, onSelect: OnChange }){

    const [value, setValue] = useState("2");
    const [error, setError] = useState<string | null>(null);

    const validityContext = useContext(Validity);
    const {validity, setValidity} = validityContext;

    useEffect(() => {
        onSelect(label, { value })
    }, []);

    return(
    <div className={`flex flex-col items-center justify-center rounded-md border border-border bg-card px-4 py-2 gap-1 w-[clamp(4.5rem,12vw,7rem)] ${value ? "text-foreground" : "text-foreground"}`}>
        <p className="text-sm text-muted-foreground">{label}</p>
        <input type="text" 
            defaultValue="2" 
            onChange={(e) => {
                const v = e.currentTarget.value;
                setValue(v);

                const result = schema.shape.numericalFromZero.safeParse(Number(v));

                if (result.success) {
                    setError(null);
                    onSelect(label, {value : v})
                    setValidity(label, true)
                } else {
                    setError("Input a number")
                    setValidity(label, false)
                }
        }} 
        size={1} 
        className={`flex text-center border border-border rounded-sm w-full min-w-0 text-sm font-mono text-primary bg-background focus:outline-none focus:border-primary`} 
        />
        { error && <span className="text-sm text-destructive">{error}</span>}
    </div>
    )
}

export default FieldEntry;