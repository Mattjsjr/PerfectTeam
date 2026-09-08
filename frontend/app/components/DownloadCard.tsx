import Podium from "./Podium";
import Crowd from "./Crowd";

function DownloadCard({csvLink, loading, buttonLabel} : {csvLink : string, loading : number, buttonLabel : string}){

    return (
    <div className={`items-center justify-center bg-card border border-border rounded-lg w-11/12 min-h-[600px] py-6 px-6 ${loading === 3 ? "flex flex-col gap-2" : "hidden"}`}>
        <a href={csvLink} download="data.csv">
            <div className="flex items-center rounded-lg bg-primary hover:bg-secondary-foreground transition-colors hover:cursor-pointer px-5 py-3 gap-2">
                <p className="text-primary-foreground font-medium">{buttonLabel}</p>
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary-foreground">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="7 10 12 15 17 10"></polyline>
                    <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
            </div>
        </a>
        <Podium />
        <Crowd />
    </div>
    );
}

export default DownloadCard;