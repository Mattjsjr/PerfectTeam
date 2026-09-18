"use client"
import { useState, useContext, useEffect } from "react";
import { OnChange } from "../types/stats";
import { ToggleInput } from "./ToggleInput";
import { Toggles } from "../context/SwitchContext";
import { useRef } from "react";
import { Validity } from "../context/FormValidityContext";
import { schema } from "../types/zod";

function StatButton({ label, onSelect } : { label: string, onSelect: OnChange }){

    const [statState, setStatState] = useState<boolean>(false);
    const toggleContext = useContext(Toggles);
    const {toggleMap, updateMap} = toggleContext;
    const hasInitialized = useRef(false);
    const validContext = useContext(Validity);
    const {validity, setValidity} = validContext;
    const [error, setError] = useState<string | null>(null);


    useEffect(() => {
        if (hasInitialized.current) return;
        hasInitialized.current = true;
        updateMap(label);
    }, [])

    return(
    <div className={`flex flex-col items-center justify-center hover:cursor-pointer rounded-md border transition-colors ${statState ? "bg-secondary border-primary px-4 py-2 text-foreground" : "border-border bg-card hover:border-primary hover:bg-accent px-4 py-2 text-foreground"}`}>
        <p onClick={(event) => {
                setStatState(!statState);
                onSelect(label, {selected: statState, value: "0"});
            }
        } className="text-sm">{label}</p>
        <input type="text" defaultValue="0" 
        onChange={
            (event) => {        
                const v = event.currentTarget.value;
                onSelect(label, {value: label, selected: statState});
                
                const result = schema.shape.numericalAny.safeParse(Number(v));
                setError(null);

                if (result.success){
                    setValidity(label, true);
                    setError(null);
                } else {
                    setValidity(label, false);
                    setError("Invalid")
                }
            } 
        } 
            size={1} className={`${statState ? "flex text-center border border-border rounded-sm w-full min-w-0 text-sm font-mono text-primary bg-background mt-2 py-1 focus:outline-none focus:border-primary" : "hidden"}`} />
        {statState && (
            <ToggleInput label="Per Point" buttonName={label}/>)
        }
        {error && (
            <span className="text-sm text-destructive">{error}</span>
        )

        }
    </div>
    )
}

export default StatButton;