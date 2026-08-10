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

import { clubById } from "../dashboardConfig";

function CustomTooltip({ active, label, metric, payload }) {
  if (!active || !payload?.length) return null;

  return (
    <div className="chartTooltip">
      <strong>{label}</strong>
      <div className="tooltipList">
        {payload.map((item) => (
          <div key={item.dataKey} className="tooltipRow">
            <span style={{ color: item.color }}>{clubById[item.dataKey]?.name ?? item.dataKey}</span>
            <strong>{metric.formatter(item.value)}</strong>
          </div>
        ))}
      </div>
    </div>
  );
}

export function MetricChart({ chartData, chartType, metric, selectedClubIds }) {
  const hasValues = chartData.some((row) =>
    selectedClubIds.some((clubId) => row[clubId] !== null && row[clubId] !== undefined),
  );

  if (!hasValues) {
    return (
      <div className="chartEmpty">
        <h3>This view is waiting on data</h3>
        <p>
          The current season range does not yet have usable values for <strong>{metric.label}</strong>.
          Try a different metric, or narrow the range to seasons where that layer exists.
        </p>
      </div>
    );
  }

  return (
    <div className="chartWrap">
      <ResponsiveContainer width="100%" height="100%">
        {chartType === "line" ? (
          <LineChart data={chartData} margin={{ top: 12, right: 12, left: 0, bottom: 18 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(28, 44, 36, 0.12)" />
            <XAxis dataKey="season" angle={-35} textAnchor="end" height={70} tick={{ fontSize: 12 }} />
            <YAxis
              reversed={metric.reverseAxis}
              tickFormatter={metric.axisTick}
              tick={{ fontSize: 12 }}
            />
            <Tooltip content={<CustomTooltip metric={metric} />} />
            <Legend formatter={(value) => clubById[value]?.name ?? value} />
            {selectedClubIds.map((clubId) => (
              <Line
                key={clubId}
                type="monotone"
                dataKey={clubId}
                name={clubById[clubId]?.name ?? clubId}
                stroke={clubById[clubId]?.color}
                strokeWidth={3}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
                connectNulls={false}
              />
            ))}
          </LineChart>
        ) : (
          <BarChart data={chartData} margin={{ top: 12, right: 12, left: 0, bottom: 18 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(28, 44, 36, 0.12)" />
            <XAxis dataKey="season" angle={-35} textAnchor="end" height={70} tick={{ fontSize: 12 }} />
            <YAxis
              reversed={metric.reverseAxis}
              tickFormatter={metric.axisTick}
              tick={{ fontSize: 12 }}
            />
            <Tooltip content={<CustomTooltip metric={metric} />} />
            <Legend formatter={(value) => clubById[value]?.name ?? value} />
            {selectedClubIds.map((clubId) => (
              <Bar
                key={clubId}
                dataKey={clubId}
                name={clubById[clubId]?.name ?? clubId}
                fill={clubById[clubId]?.color}
                radius={[8, 8, 0, 0]}
              />
            ))}
          </BarChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}
