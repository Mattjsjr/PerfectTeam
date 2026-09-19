"use client"
import StatButton from "./StatButton";
import FieldEntry from "./FieldEntry";
import { useEffect, useState } from "react";
import { OnChange } from "../types/stats";
import { StatEntry } from "../types/stats";

function StatButtonContainer({ label, endpoint, loading, submit } : {label : string, endpoint: string, loading: number, submit : OnChange}){

    const [stats, setStats] = useState<Record<string, string[]>>({});
    const [demo, setDemo] = useState<boolean>(label === "Demo");

    function handleSelect(stat: string, patch : Partial<StatEntry>){
        submit(stat, patch);
    }

    useEffect(() => {
        if (!demo){
            async function loadHome() {
                loading = 0;
                try {
                    const res = await fetch(`http://localhost:5000${endpoint}`)
                    const data = await res.json()
                    console.log(data);
                    setStats(data);

                } catch (e) {
                    console.log(`Error fetching at home ${e}`)
                    setDemo(true);
                }
            }
            loading = 1;
            loadHome();
        }

    }, []);


    return(
    <div className={loading === 1
        ? `flex flex-col gap-6 flex-wrap items-center justify-center w-4/5 py-6 px-6 bg-card border border-border text-foreground rounded-lg`
        : loading === 0
            ? "flex flex-col gap-6 flex-wrap items-center justify-center w-4/5 py-6 px-6 bg-card border border-border text-foreground rounded-lg"
            : "hidden"}>

        {
            // Renders for demo purposes
            !demo ? (
            <>
                <h1 className="font-heading font-bold text-2xl tracking-wide">{label}</h1>
                <div className="flex flex-row gap-3 flex-wrap items-center justify-center">
                    {(stats.stat_button ?? []).map((stat, index) => (
                        <StatButton
                        key={index}
                        label={stat}
                        onSelect={handleSelect}>
                        </StatButton>
                    ))}
                </div>
                <div className="flex flex-row gap-3 flex-wrap items-center justify-center">
                    {(stats.field_entry ?? []).map((stat, index) => (
                        <FieldEntry
                        key={index}
                        label={stat}
                        onSelect={handleSelect}>
                        </FieldEntry>
                    ))}
                </div>
            </>

            ) : (
            <>

                <h1 className="font-heading font-bold text-2xl tracking-wide">Settings</h1>
                <div className="flex flex-row gap-3 flex-wrap items-center justify-center">
                {(["Teams", "QB", "RB", "WR", "TE", "DB", "DL", "LB", "K", "DST"]).map((stat, index) => (
                    <FieldEntry
                    key={index}
                    label={stat}
                    onSelect={handleSelect}>
                    </FieldEntry>
                ))}
                </div>
                <h1 className="font-heading font-bold text-2xl tracking-wide">Defense</h1>
                <div className="flex flex-row gap-3 flex-wrap items-center justify-center">
                    
                    {(["Team Interceptions", "Team Fumble Recoveries", "Team Sacks", "Team Forced Fumbles", "Tackle Solo", "Tackle Assist", "Sack", "Pass Defended", "Interception", "Fumble Force", "Fumble Recovery", "Defensive TD"]).map((stat, index) => (
                        <StatButton
                        key={index}
                        label={stat}
                        onSelect={handleSelect}>
                        </StatButton>
                    ))}
                </div>

                <h1 className="font-heading font-bold text-2xl tracking-wide">Offense</h1>
                <div className="flex flex-row gap-3 flex-wrap items-center justify-center">
                    {(["Pass Attempts", "Completions", "Passing Yards", "Passing TDs", "Interceptions Thrown", "Rush Attempts", "Rushing Yards", "Rushing TDs", "Receptions", "Receiving Yards", "Receiving TDs", "Fumbles Lost", "Field Goals Made", "Field Goal Attempts", "Extra Points Made"]).map((stat, index) => (
                        <StatButton
                        key={index}
                        label={stat}
                        onSelect={handleSelect}>
                        </StatButton>
                    ))}
                </div>

            </>
            )
        }
    </div>

    )
}

export default StatButtonContainer;