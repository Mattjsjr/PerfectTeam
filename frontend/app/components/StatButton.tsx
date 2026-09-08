"use client"
import { useState, useContext, useEffect } from "react";
import { OnChange } from "../types/stats";
import { ToggleInput } from "./ToggleInput";
import { Toggles } from "../context/SwitchContext";
import { useRef } from "react";

function StatButton({ label, onSelect } : { label: string, onSelect: OnChange }){

    const [statState, setStatState] = useState<boolean>(false);
    const toggleContext = useContext(Toggles);
    const {toggleMap, updateMap} = toggleContext;
    const hasInitialized = useRef(false);

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
        <input type="text" defaultValue="0" onChange={(event) => onSelect(label, {value: event.currentTarget.value, selected: statState})} size={1} className={`${statState ? "flex text-center border border-border rounded-sm w-full min-w-0 text-sm font-mono text-primary bg-background mt-2 py-1 focus:outline-none focus:border-primary" : "hidden"}`} />
        {statState && (
            <ToggleInput label="Per Point" buttonName={label}/>
        )}
    </div>
    )
}

export default StatButton;