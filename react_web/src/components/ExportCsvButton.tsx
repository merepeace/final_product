import { Button, Tooltip } from "@mui/material";
import DownloadIcon from "@mui/icons-material/Download";
import { downloadCsv } from "../utils/csv";
import type { CsvColumn } from "../utils/csv";

interface Props<T> {
  basename: string;
  rows: T[];
  columns: CsvColumn<T>[];
  disabled?: boolean;
  label?: string;
}

export default function ExportCsvButton<T>({
  basename,
  rows,
  columns,
  disabled,
  label = "Export CSV",
}: Props<T>) {
  const isEmpty = rows.length === 0;
  const button = (
    <span>
      <Button
        variant="outlined"
        startIcon={<DownloadIcon />}
        onClick={() => downloadCsv(basename, rows, columns)}
        disabled={disabled || isEmpty}
      >
        {label}
      </Button>
    </span>
  );
  if (isEmpty) {
    return <Tooltip title="Nothing to export">{button}</Tooltip>;
  }
  return button;
}
