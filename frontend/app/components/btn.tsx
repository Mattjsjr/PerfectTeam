"use client"

function Btn({label, action, loading, appearOnPage, validInputMap} : {label: string, action: () => void, loading: number, appearOnPage : number, validInputMap : Record<string, boolean>} ){
    
    let blocked = false;

    for (const validity in validInputMap){
        if (!validInputMap[validity]){
            blocked = true;
            break;
        }
    }
    
    return (
        <>
            <div onClick={blocked ? undefined : action} className={
            loading === appearOnPage
                ? `z-1 relative flex items-center justify-center px-6 py-3 rounded-lg bg-primary text-primary-foreground transition-colors ${
                    blocked ? "opacity-50 cursor-default" : "hover:cursor-pointer hover:bg-secondary-foreground"
                }`
                : "hidden"
            }>
                <p className="font-medium">{label}</p>
            </div>
        </>
    );
}

export default Btn;