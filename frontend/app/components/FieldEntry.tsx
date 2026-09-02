"use client"
import { useEffect, useState } from "react";
import { OnChange } from "../types/stats";
import React from "react";


function FieldEntry({ label, onSelect } : { label: string, onSelect: OnChange }){

    const [value, setValue] = useState("2");

    useEffect(() => {
        onSelect(label, { value })
    }, [])

    return(
        <div className={`flex flex-col items-center justify-center rounded-sm ${value ?  "bg-[#0d1826] p-2 text-white" : " bg-[#0d1826] p-2 text-white"}`}>
            <p>{label}</p>
            <input type="text" defaultValue="2" onChange={(e) => {
                const v = e.currentTarget.value;
                setValue(v);
                onSelect(label, {value : v});
            }} size={1} className={`flex text-center border border-solid rounded-sm w-full min-w-0 text-sm`} />
        </div>
    )
}

export default FieldEntry;