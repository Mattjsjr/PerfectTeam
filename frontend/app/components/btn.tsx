"use client"

function Btn({label, action, loading} : {label: string, action: () => void, loading: number} ){
    return (
        <>
            <div onClick={action} className={loading === 1 ? "flex items-center justify-center px-6 py-3 rounded-lg bg-primary text-primary-foreground hover:cursor-pointer hover:bg-secondary-foreground transition-colors" : "hidden"}>
                <p className="font-medium">{label}</p>
            </div>
        </>
    );
}

export default Btn;