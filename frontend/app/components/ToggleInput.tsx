import { Switch } from "./Toggle";

export function ToggleInput({label, buttonName} : {label : string, buttonName : string}){

    return(
        <div className="flex flex-col items-center justify-center">
            <div className="flex items-center justify-between">
                <p>{label}</p>
                <Switch buttonName={buttonName} />
            </div>
        </div>
    )
}