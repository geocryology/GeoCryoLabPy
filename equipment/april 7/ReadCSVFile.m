function Data = ReadCSVFile(FileName, Rs)

% Usage: Data = ReadCSVFile(FileName)

% Author Hervé Gagnon 2017.

% Read Header

if (nargin < 1)
    error('Usage: Data = ReadCSVFile(FileName);');
end

FileID = fopen(FileName);

if (FileID == -1)
   error('Unable to open file %s.', FileName); 
end

% Skip first line
textscan(FileID, '%s', 1, 'Delimiter', '\n');

% Read time and date
Time = textscan(FileID, '%s', 7, 'Delimiter', 'T:-');
Data.Date.Year   = Time{1}{2};
Data.Date.Month  = Time{1}{3};
Data.Date.Day    = Time{1}{4};
Data.Time.Hour   = Time{1}{5};
Data.Time.Minute = Time{1}{6};
Data.Time.Second = Time{1}{7};

% Read Rs value.
Rstxt   = textscan(FileID, '%s', 4, 'Delimiter', ' ');
if (exist('Rs', 'var'))
    Data.Rs = Rs;
else
    Data.Rs = str2double(Rstxt{1}{3});
end

Data.Rs

% Skip four lines
textscan(FileID, '%s', 5, 'Delimiter', '\n');

% Read Power Source Value
PowerSource      = textscan(FileID, '%s', 2, 'Delimiter', ':');
Data.PowerSource = str2double(PowerSource{1}{2});

% Skip four lines
textscan(FileID, '%s', 5, 'Delimiter', '\n');

% Read measurements
Measurements = textscan(FileID, '%f %f %f %f %f %f %f %f %f %f %f', 'Delimiter', ',');

Data.Frequency           = Measurements{1};
Data.Va_real             = Measurements{2};
Data.Va_imag             = Measurements{3};
Data.Vb_real             = Measurements{4};
Data.Vb_imag             = Measurements{5};
Data.Va_magnitude        = Measurements{6};
Data.Va_phase            = Measurements{7};
Data.Vb_magnitude        = Measurements{8};
Data.Vb_phase            = Measurements{9};
Data.Impedance_magnitude = Measurements{10};
Data.Impedance_phase     = Measurements{11};

Data.Va                  = Data.Va_real + 1i*Data.Va_imag;
Data.Vb                  = Data.Vb_real + 1i*Data.Vb_imag;
Data.Impedance           = Data.Rs*(Data.Va - Data.Vb)./Data.Vb;

Data = rmfield(Data, {'Va_real', 'Va_imag', 'Va_magnitude', 'Va_phase', ...
                      'Vb_real', 'Vb_imag', 'Vb_magnitude', 'Vb_phase', ...
                      'Impedance_magnitude', 'Impedance_phase'});

fclose(FileID);
