import {motion} from "framer-motion";


export default function PlayBookO({delay, strokeDuration, positionX, positionY} : {delay : number, strokeDuration : number, positionX : number, positionY : number}){

    function generateRandNum(min : number, max : number){
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }

    // 85, 92 | 85, 92
    //82, 87 | 82, 88

    return (
        <>
            <svg viewBox="0 0 125 125" className={`absolute w-[5%]`} style={{ left: `${positionX}%`, top: `${positionY}%` }}>
            <motion.circle
                cx={62.5}
                cy={62.5}
                r={generateRandNum(50, 60)}
                stroke="currentColor"
                strokeWidth={8}
                fill="none"
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: strokeDuration, ease: "easeInOut", delay: delay }}
            />
            </svg>
        </>
    )
}

