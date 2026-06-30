function time = create_daily_datetime_vector(startYear, numYears)
%CREATE_DAILY_DATETIME_VECTOR Create a daily datetime vector from year span.
%
% time = create_daily_datetime_vector(startYear, numYears)
%
% Inputs
%   startYear - first calendar year, for example 2001
%   numYears  - number of complete calendar years to include
%
% Output
%   time      - column datetime vector with daily time step from Jan 1 of
%               startYear through Dec 31 of startYear + numYears - 1.
%
% Example
%   time = create_daily_datetime_vector(2001, 3);
%   % returns daily dates from 2001-01-01 through 2003-12-31

arguments
    startYear (1, 1) {mustBeInteger, mustBeFinite}
    numYears (1, 1) {mustBeInteger, mustBePositive}
end

startDate = datetime(startYear, 1, 1);
endDate = datetime(startYear + numYears, 1, 1) - days(1);

time = (startDate:days(1):endDate).';
end
