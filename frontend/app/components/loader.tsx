import PlayBookX from "./PlayBookX";
import PlayBookO from "./PlayBookO"

function Loader({state} : {state: number}){

    const lineDrawDuration = .15
    const delayX = 11 * lineDrawDuration * 2
    const play1 = {
        'x' : [[16, 27], [39, 20], [35, 37], [47, 37], [56, 36], [66, 20], [31, 48], [41, 48], [47, 48], [54, 48], [66, 48]],
        'o' : [[15, 55], [30, 55], [37, 55], [44, 55], [51, 55], [58, 55], [65, 55], [78, 55], [75, 63], [50, 70], [57, 70]]
    }

    if (state !== 2) return null;

    return (
        <div className={state === 2 ? "relative gap-4 w-4/5 py-4 px-4  h-[80vh]" : "hidden"}>
            {Array.from({ length: 11 }).map((_, i) => (
                <PlayBookO delay={i * lineDrawDuration * 2} 
                strokeDuration={lineDrawDuration} 
                positionX={play1['o'][i][0]}
                positionY={play1['o'][i][1]}
                />
            ))}

            {Array.from({ length: 11 }).map((_, i) => (
                <PlayBookX delay={i * lineDrawDuration * 2} 
                strokeDuration={lineDrawDuration} 
                positionX={play1['x'][i][0]}
                positionY={play1['x'][i][1]}
                />
            ))}

        </div>
    )
}

export default Loader;