"use client"

function Btn({label, action, loading} : {label: string, action: () => void, loading: number} ){
    return (
        <>
            <div onClick={action} className={loading === 1 ?"items-center justify-center p-2 rounded-sm bg-[#4e55e3] text-white hover:cursor-pointer hover:text-white hover:bg-[#0d1826]" : "hidden"}>
                <p>{label}</p>
            </div>
        </>
    );
}

export default Btn;