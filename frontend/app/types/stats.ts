export type StatEntry = {
    selected: boolean;
    value: string;
}

export type OnChange = (key: string, patch: Partial<StatEntry>) => void;

export type StatSelections = Record<string, boolean>;
