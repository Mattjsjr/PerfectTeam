import { createContext } from "react";
import React from "react";

/*
Creates context for the toggles on the stat buttons
*/


interface ToggleMap {
    toggleMap : Record<string, boolean>;
    updateMap : (buttonName : string) => void
}

export const Toggles = React.createContext<ToggleMap>({toggleMap: {}, updateMap: (buttonName : string) => {}});

