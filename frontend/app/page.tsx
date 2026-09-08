"use client"

import StatButtonContainer from "./components/StatButtonContainer";
import Btn from "./components/btn";
import Loader from "./components/loader";
import { useState, useEffect, useRef } from "react";
import { StatEntry } from "./types/stats";
import {Toggles} from "./context/SwitchContext"
import DownloadCard from "./components/DownloadCard";

export default function Home() {

  /*
  States
  1 : Display normal content
  2 : Loading
  3 : Loaded
  */
  const [mainContentState, setMainContentState] = useState(1)
  const selectedStats : Record<string, StatEntry> = {}
  const settings = useRef<Record<string, StatEntry>> ({})
  const [toggleMap, setToggleMap] = useState<Record<string, boolean>>({})
  const [csvUrl, setCsvUrl] = useState("https://google.com");

  function updateToggleMap(buttonName : string){
    setToggleMap(prev => {
      if (buttonName in prev) {
        return { ...prev, [buttonName] : !prev[buttonName]}
      } else {
        return {...prev, [buttonName] : false}
      }
    })
  }

  async function submit(){
    setMainContentState(2);

    try {
      const response = await fetch("http://localhost:5000/submit", {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({"selectedStats":selectedStats, "selectedSettings":settings.current, "selectedToggles": toggleMap})
      })

      const blob = await response.blob();
      setCsvUrl(window.URL.createObjectURL(blob));
      setMainContentState(3);

    } catch (error){
      console.log(`Error sending the stats up ${error}`)
    }
  }

  function getStats(stat: string, patch : Partial<StatEntry>){
    const existing = selectedStats[stat] ?? {selected: true, value: "0"};
    selectedStats[stat] = { ...existing, ...patch };
  }

  function getSettings(setting: string, patch : Partial<StatEntry>){
    const existing = settings.current[setting] ?? {value: "2"}
    settings.current[setting] = {...existing, ...patch};
    console.log(settings);
    console.log("")
  }

  return (

    <>
      <div className="flex flex-col flex-1 items-center justify-start bg-background font-sans gap-6">
        <header className="flex items-center justify-center w-full px-6 py-6 bg-sidebar text-sidebar-foreground border-b border-sidebar-border">
          <h1 className="font-heading text-3xl tracking-wide">Perfect Team</h1>
        </header>
        <main className="flex flex-col items-center w-full max-w-4xl px-4 gap-6">
          <DownloadCard csvLink={csvUrl} loading={mainContentState} buttonLabel="Your Strategy"></DownloadCard>
          <Toggles.Provider value={{toggleMap: toggleMap, updateMap: updateToggleMap}}>
            <StatButtonContainer label="League Settings" endpoint="/settings" loading={mainContentState} submit={getSettings}></StatButtonContainer>
            <StatButtonContainer label="Offensive Stats" endpoint="/offense" loading={mainContentState} submit={getStats}></StatButtonContainer>
            <StatButtonContainer label="Defensive Stats" endpoint="/defense" loading={mainContentState} submit={getStats}></StatButtonContainer>
          </Toggles.Provider>
        </main>
        <Loader state={mainContentState}></Loader>
        <div className="pb-10">
          <Btn label="Calculate" action={submit} loading={mainContentState}></Btn>
        </div>
      </div>
    </>
  );
}
