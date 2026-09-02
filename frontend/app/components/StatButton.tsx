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
        <div className={`flex flex-col items-center justify-center hover:cursor-pointer rounded-sm ${statState ?  "bg-[#4e55e3] p-2 text-white" : "hover:bg-[#4e55e3] bg-[#0d1826] p-2 text-white"}`}>
            <p onClick={(event) => {
                    setStatState(!statState);
                    onSelect(label, {selected: statState, value: "0"});
                }
            }>{label}</p>
            <input type="text" defaultValue="0" onChange={(event) => onSelect(label, {value: event.currentTarget.value, selected: statState})} size={1} className={` ${statState ? "flex text-center border border-solid rounded-sm w-full min-w-0 text-sm" : "hidden" }`} />
            {statState && (
                <ToggleInput label="Per Point" buttonName={label}/>
            )}
        </div>
    )
}

export default StatButton;