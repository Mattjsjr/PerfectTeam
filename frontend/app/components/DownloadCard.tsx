import podium from '../../src/assets/images/podium.png'


function DownloadCard({csvLink, loading, buttonLabel} : {csvLink : string, loading : number, buttonLabel : string}){

    return (
        <div className={`items-center justify-center bg-[#051122] w-4/5 py-4 px-4 ${loading === 3 ? "flex flex-col" : "hidden"}`} >
            <a href={csvLink} download="data.csv">
                <div className="flex items-center align-center rounded-md dark:bg-[#4e55e3] hover:cursor-pointer p-4 gap-1">
                    <p className="text-white">{buttonLabel}</p>
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                        <polyline points="7 10 12 15 17 10"></polyline>
                        <line x1="12" y1="15" x2="12" y2="3"></line>
                    </svg>
                </div>
            </a>
            <img src={podium.src ?? podium}></img>
        </div>
    );
}

export default DownloadCard;