function DownloadCard({csvLink, loading} : {csvLink : string, loading : number}){

    return (
        <div className={`items-center justify-center bg-[#051122] w-4/5 py-4 px-4 ${loading === 3 ? "flex" : "hidden"}`} >
            <a href={csvLink} download="data.csv">
                <p className="text-white">CSV Download</p>
            </a>
        </div>
    );
}

export default DownloadCard;