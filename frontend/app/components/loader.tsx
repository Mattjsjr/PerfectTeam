import React from "react";

function Loader({state} : {state: number}){
    return (
        <div className={state === 2 ? "flex flex-row gap-4 flex-wrap items-center justify-center w-4/5 py-4 px-4 bg-[#051122] rounded-sm h-[80vh]" : "hidden"}>
            <div className="h-8 w-8 rounded-full border-4 border-gray-200 border-t-blue-600 [animation:spin_1s_linear_infinite]" />
        </div>
    )
}

export default Loader;