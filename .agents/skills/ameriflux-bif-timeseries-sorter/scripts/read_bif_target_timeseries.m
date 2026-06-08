function data = read_bif_target_timeseries(outputDir, makePlot)
%READ_BIF_TARGET_TIMESERIES Read AmeriFlux BIF target series for plotting.
%
% data = read_bif_target_timeseries(outputDir)
% data = read_bif_target_timeseries(outputDir, true)
%
% The input directory should be the output from sort_bif_timeseries.py, for
% example result/US-Ne3/bif_timeseries. The function reads:
%   target_timeseries/total_lai.csv
%   target_timeseries/leaf_mass_per_area.csv
%   target_timeseries/aboveground_biomass.csv
%   target_timeseries/canopy_height.csv
%
% Returned tables include Time as datetime and Value as double. Original BIF
% values, units, comments, and qualifiers are preserved in the table columns.

if nargin < 1 || isempty(outputDir)
    outputDir = fullfile("result", "US-Ne3", "bif_timeseries");
end
if nargin < 2 || isempty(makePlot)
    makePlot = false;
end

targetDir = fullfile(outputDir, "target_timeseries");
series = [
    struct("name", "total_lai", "label", "Total LAI")
    struct("name", "leaf_mass_per_area", "label", "Leaf mass per area")
    struct("name", "aboveground_biomass", "label", "Above-ground biomass")
    struct("name", "canopy_height", "label", "Canopy height")
];

data = struct();
data.outputDir = string(outputDir);
data.targetDir = string(targetDir);
data.files = struct();

for i = 1:numel(series)
    name = series(i).name;
    filePath = fullfile(targetDir, name + ".csv");
    data.files.(name) = string(filePath);

    if ~isfile(filePath)
        warning("read_bif_target_timeseries:MissingFile", "Missing target time-series file: %s", filePath);
        data.(name) = table();
        continue
    end

    T = readtable(filePath, "TextType", "string");
    if ismember("TIMESTAMP", T.Properties.VariableNames)
        T.Time = parseBifTimestamp(T.TIMESTAMP);
    end
    if ismember("VALUE_NUMERIC", T.Properties.VariableNames)
        if isnumeric(T.VALUE_NUMERIC)
            T.Value = T.VALUE_NUMERIC;
        else
            T.Value = str2double(string(T.VALUE_NUMERIC));
        end
    end
    data.(name) = T;
end

if makePlot
    plotTargetSeries(data, series);
end
end

function t = parseBifTimestamp(values)
values = string(values);
t = NaT(numel(values), 1);
formats = ["yyyy-MM-dd HH:mm:ss", "yyyy-MM-dd HH:mm", "yyyy-MM-dd", "yyyy"];

for i = 1:numel(values)
    value = strtrim(values(i));
    if strlength(value) == 0 || ismissing(value)
        continue
    end
    for j = 1:numel(formats)
        try
            parsed = datetime(value, "InputFormat", formats(j));
            if ~isnat(parsed)
                t(i) = parsed;
                break
            end
        catch
        end
    end
end
end

function plotTargetSeries(data, series)
figure;
tiledlayout(numel(series), 1, "TileSpacing", "compact");

for i = 1:numel(series)
    name = series(i).name;
    nexttile;
    if ~isfield(data, name) || isempty(data.(name)) || height(data.(name)) == 0
        title(series(i).label);
        ylabel("missing");
        continue
    end

    T = data.(name);
    if ~ismember("Time", T.Properties.VariableNames) || ~ismember("Value", T.Properties.VariableNames)
        title(series(i).label);
        ylabel("unreadable");
        continue
    end

    groupColumn = chooseGroupColumn(T);
    if groupColumn ~= ""
        groups = unique(string(T.(groupColumn)));
        hold on
        for g = 1:numel(groups)
            mask = string(T.(groupColumn)) == groups(g);
            plot(T.Time(mask), T.Value(mask), "o-", "DisplayName", groups(g));
        end
        hold off
        legend("Location", "best");
    else
        plot(T.Time, T.Value, "o-");
    end

    title(series(i).label);
    ylabel(valueLabel(T));
    grid on
end
xlabel("Time");
end

function groupColumn = chooseGroupColumn(T)
candidateColumns = ["AG_BIOMASS_CROP_ORGAN", "HEIGHTC_STATISTIC", "LAI_TYPE", "LMA_SPP"];
groupColumn = "";
for i = 1:numel(candidateColumns)
    column = candidateColumns(i);
    if ismember(column, T.Properties.VariableNames)
        values = string(T.(column));
        values = values(strlength(values) > 0 & ~ismissing(values));
        if numel(unique(values)) > 1
            groupColumn = column;
            return
        end
    end
end
end

function label = valueLabel(T)
label = "value";
if ismember("UNIT", T.Properties.VariableNames)
    units = string(T.UNIT);
    units = units(strlength(units) > 0 & ~ismissing(units));
    if ~isempty(units)
        label = "value (" + units(1) + ")";
    end
end
end
