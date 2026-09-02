"use client"
import StatButton from "./StatButton";
import FieldEntry from "./FieldEntry";
import { useEffect, useState } from "react";
import { OnChange } from "../types/stats";
import { StatEntry } from "../types/stats";

function StatButtonContainer({ label, endpoint, loading, submit } : {label : string, endpoint: string, loading: number, submit : OnChange}){

    const [stats, setStats] = useState<Record<string, string[]>>({});

    function handleSelect(stat: string, patch : Partial<StatEntry>){
        submit(stat, patch);
    }

    useEffect(() => {

        async function loadHome() {
            loading = 0;
            try {
                const res = await fetch(`http://localhost:5000${endpoint}`)
                const data = await res.json()
                setStats(data);

            } catch (e) {
                console.log(`Error fetching at home ${e}`)
            }
        }
        loading = 1;
        loadHome();
    }, []);


    return(
        <div className={loading === 1 
        ? `flex flex-col gap-4 flex-wrap items-center justify-center w-4/5 py-4 px-4 bg-[#051122] text-white rounded-sm` 
        : loading=== 0 
            ? "flex flex-col gap-4 flex-wrap items-center justify-center w-4/5 py-4 px-4 bg-[#051122] text-white rounded-sm"
            : "hidden"}>
            <h1 className="font-bold text-xl">{label}</h1>
            <div className="flex flex-row gap-4 flex-wrap items-center justify-center">
                {(stats.stat_button ?? []).map((stat, index) => (
                    <StatButton 
                    key={index} 
                    label={stat} 
                    onSelect={handleSelect}>
                    </StatButton>
                ))}
            </div>
            <div className="flex flex-row gap-4 flex-wrap items-center justify-center">
                {(stats.field_entry ?? []).map((stat, index) => (
                    <FieldEntry 
                    key={index} 
                    label={stat} 
                    onSelect={handleSelect}>
                    </FieldEntry>
                ))}
            </div>
        </div>

    )
}

export default StatButtonContainer;