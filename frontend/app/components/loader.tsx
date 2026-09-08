import PlayBookX from "./PlayBookX";
import PlayBookO from "./PlayBookO"

function Loader({state} : {state: number}){

    const lineDrawDuration = .3
    const play1 = {
        'x' : [[16, 25], [39, 18], [35, 35], [47, 35], [56, 34], [66, 18], [31, 46], [41, 46], [47, 46], [54, 46], [66, 46]],
        'o' : [[15, 57], [30, 57], [37, 57], [44, 57], [51, 57], [58, 57], [65, 57], [78, 57], [75, 65], [50, 72], [57, 72]]
    }

    if (state !== 2) return null;

    return (
        <div className={state === 2 ? "relative w-4/5 h-[80vh] rounded-lg border border-border bg-card overflow-hidden" : "hidden"}>
            {Array.from({ length: 11 }).map((_, i) => (
                <PlayBookO key={`o-${i}`}
                delay={i * lineDrawDuration * 2}
                strokeDuration={lineDrawDuration}
                positionX={play1['o'][i][0]}
                positionY={play1['o'][i][1]}
                />
            ))}

            {Array.from({ length: 11 }).map((_, i) => (
                <PlayBookX key={`x-${i}`}
                delay={i * lineDrawDuration * 2}
                strokeDuration={lineDrawDuration}
                positionX={play1['x'][i][0]}
                positionY={play1['x'][i][1]}
                />
            ))}

        </div>
    )
}

export default Loader;