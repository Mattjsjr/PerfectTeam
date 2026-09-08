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
    <div className={`flex flex-col items-center justify-center rounded-md border border-border bg-card px-4 py-2 gap-1 ${value ? "text-foreground" : "text-foreground"}`}>
        <p className="text-sm text-muted-foreground">{label}</p>
        <input type="text" defaultValue="2" onChange={(e) => {
            const v = e.currentTarget.value;
            setValue(v);
            onSelect(label, {value : v});
        }} size={1} className={`flex text-center border border-border rounded-sm w-full min-w-0 text-sm font-mono text-primary bg-background focus:outline-none focus:border-primary`} />
    </div>
    )
}

export default FieldEntry;