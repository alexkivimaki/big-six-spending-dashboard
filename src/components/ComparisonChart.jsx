import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { clubConfigById } from "../config/clubConfig";

function ChartTooltip({ active, payload, label, metric }) {
  if (!active || !payload?.length) return null;

  return (
    <div className="chartTooltip">
      <strong>{label}</strong>
      <div className="tooltipRows">
        {payload.map((entry) => (
          <div key={entry.dataKey} className="tooltipRow">
            <span style={{ color: entry.color }}>{clubConfigById[entry.dataKey]?.name}</span>
            <strong>{metric.formatValue(entry.value)}</strong>
          </div>
        ))}
      </div>
    </div>
  );
}

export function ComparisonChart({ chartData, chartType, metric, selectedClubIds }) {
  const hasValues = chartData.some((row) => selectedClubIds.some((clubId) => row[clubId] !== null));

  if (!hasValues) {
    return (
      <div className="emptyState">
        <h3>No usable observations in this view</h3>
        <p>Try a different metric or a different season range.</p>
      </div>
    );
  }

  return (
    <div className="chartCanvas">
      <ResponsiveContainer width="100%" height="100%">
        {chartType === "line" ? (
          <LineChart data={chartData} margin={{ top: 10, right: 8, left: 0, bottom: 28 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(19, 34, 28, 0.12)" />
            <XAxis dataKey="season" angle={-35} textAnchor="end" height={72} tick={{ fontSize: 12 }} />
            <YAxis reversed={metric.reverseAxis} tickFormatter={metric.axisTick} tick={{ fontSize: 12 }} />
            <Tooltip content={<ChartTooltip metric={metric} />} />
            <Legend formatter={(value) => clubConfigById[value]?.shortName ?? value} />
            {selectedClubIds.map((clubId) => (
              <Line
                key={clubId}
                dataKey={clubId}
                stroke={clubConfigById[clubId].colors.primary}
                strokeWidth={3}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
                connectNulls={false}
              />
            ))}
          </LineChart>
        ) : (
          <BarChart data={chartData} margin={{ top: 10, right: 8, left: 0, bottom: 28 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(19, 34, 28, 0.12)" />
            <XAxis dataKey="season" angle={-35} textAnchor="end" height={72} tick={{ fontSize: 12 }} />
            <YAxis reversed={metric.reverseAxis} tickFormatter={metric.axisTick} tick={{ fontSize: 12 }} />
            <Tooltip content={<ChartTooltip metric={metric} />} />
            <Legend formatter={(value) => clubConfigById[value]?.shortName ?? value} />
            {selectedClubIds.map((clubId) => (
              <Bar
                key={clubId}
                dataKey={clubId}
                fill={clubConfigById[clubId].colors.primary}
                radius={[8, 8, 0, 0]}
              />
            ))}
          </BarChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}
