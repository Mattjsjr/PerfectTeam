import {motion} from "framer-motion";


export default function PlayBookX({delay, strokeDuration, positionX, positionY} : {delay : number, strokeDuration : number, positionX : number, positionY : number}){

    function generateMiddle(min : number, max : number){
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }


    console.log(positionX)
    console.log(positionY)

    // 85, 92 | 85, 92
    //82, 87 | 82, 88

    return (
        <>
            <svg viewBox="0 0 125 125" className="w-[4%] absolute" style={{ left: `${positionX}%`, top: `${positionY}%` }}>
                <motion.path
                    d={`M 0 0 C 45 42, ${generateMiddle(40, 100)} ${generateMiddle(49, 100)}, 120 125`}
                    stroke="currentColor"
                    strokeWidth={8}
                    fill="none"
                    initial={{ pathLength: 0 }}
                    animate={{ pathLength: 1 }}
                    transition={{ duration: strokeDuration, ease: "easeInOut", delay: delay }}
                />
                <motion.path
                    d={`M 125 0 C 83 42,  ${generateMiddle(40, 100)} ${generateMiddle(40, 100)}, 0 125`}
                    stroke="currentColor"
                    strokeWidth={8}
                    fill="none"
                    initial={{ pathLength: 0 }}
                    animate={{ pathLength: 1 }}
                    transition={{ duration: strokeDuration, ease: "easeInOut", delay: strokeDuration + delay }}
                />
            </svg>
        </>
    )
}

