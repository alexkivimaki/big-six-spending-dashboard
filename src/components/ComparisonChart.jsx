import { useEffect, useMemo, useState } from "react";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { clubConfigById } from "../config/clubConfig";
import { VALUE_BASIS } from "../config/valueBasis";
import { ClubChartMarker, ClubMarker } from "./ClubMarker";

function dedupePayload(payload) {
  const seen = new Set();
  return payload.filter((entry) => {
    if (seen.has(entry.dataKey)) return false;
    seen.add(entry.dataKey);
    return true;
  });
}

function ActiveMarkerDot({ cx, cy, club }) {
  if (cx === undefined || cy === undefined) return null;
  return (
    <g transform={`translate(${cx - 9}, ${cy - 9})`}>
      <ClubChartMarker club={club} size={18} />
    </g>
  );
}

function ChartTooltip({ active, payload, label, metric, valueBasis, displayCurrency }) {
  if (!active || !payload?.length) return null;
  const rows = dedupePayload(payload);

  return (
    <div className="chartTooltip">
      <div className="chartTooltipHeader">
        <strong>{label}</strong>
        <small>{metric.label}</small>
      </div>
      <div className="tooltipRows">
        {rows.map((entry) => {
          const club = clubConfigById[entry.dataKey];
          return (
            <div key={entry.dataKey} className="tooltipRow">
              <span className="tooltipClub">
                <ClubMarker club={club} size={16} />
                {club?.name ?? entry.dataKey}
              </span>
              <strong>{metric.formatValue(entry.value, { displayCurrency })}</strong>
            </div>
          );
        })}
      </div>
      {valueBasis === VALUE_BASIS.inflationAdjusted && metric.format === "percentage" ? (
        <small className="chartTooltipFootnote">Inflation does not change same-period ratios.</small>
      ) : null}
    </div>
  );
}

function ChartLegend({ selectedClubIds }) {
  return (
    <div className="chartLegend">
      {selectedClubIds.map((clubId) => {
        const club = clubConfigById[clubId];
        return (
          <div key={clubId} className="chartLegendItem">
            <ClubMarker club={club} size={16} />
            <span>{club.shortName}</span>
          </div>
        );
      })}
    </div>
  );
}

function renderLineSeries(clubId) {
  const club = clubConfigById[clubId];
  const activeDot = (props) => <ActiveMarkerDot {...props} club={club} />;
  const lineWidth = club.visuals.chart.lineWidth ?? 3;
  const haloWidth = club.visuals.chart.haloWidth ?? lineWidth + 3;

  if (club.visuals.chart.halo) {
    return [
      <Line
        key={`${clubId}-halo`}
        dataKey={clubId}
        stroke={club.visuals.chart.halo}
        strokeWidth={haloWidth}
        dot={false}
        activeDot={false}
        connectNulls={false}
        name={club.shortName}
      />,
      <Line
        key={clubId}
        dataKey={clubId}
        stroke={club.visuals.chart.line}
        strokeWidth={lineWidth}
        dot={false}
        activeDot={activeDot}
        connectNulls={false}
        name={club.shortName}
      />,
    ];
  }

  return (
    <Line
      key={clubId}
      dataKey={clubId}
      stroke={club.visuals.chart.line}
      strokeWidth={lineWidth}
      dot={false}
      activeDot={activeDot}
      connectNulls={false}
      name={club.shortName}
    />
  );
}

export function ComparisonChart({
  chartData,
  chartType,
  coverage,
  displayCurrency,
  metric,
  selectedClubIds,
  showLegend = true,
  valueBasis,
}) {
  const [isVerySmallScreen, setIsVerySmallScreen] = useState(() =>
    typeof window !== "undefined" ? window.matchMedia("(max-width: 560px)").matches : false,
  );

  useEffect(() => {
    if (typeof window === "undefined") return undefined;

    const mediaQuery = window.matchMedia("(max-width: 560px)");
    const handleChange = (event) => setIsVerySmallScreen(event.matches);

    setIsVerySmallScreen(mediaQuery.matches);
    mediaQuery.addEventListener("change", handleChange);

    return () => mediaQuery.removeEventListener("change", handleChange);
  }, []);

  const seasonTickInterval = useMemo(() => {
    if (!isVerySmallScreen) return 0;
    if (chartData.length >= 12) return 1;
    if (chartData.length >= 8) return 0;
    return 0;
  }, [chartData.length, isVerySmallScreen]);

  const hasValues = chartData.some((row) => selectedClubIds.some((clubId) => row[clubId] !== null));

  if (!hasValues) {
    return (
      <div className="emptyState">
        <h3>{coverage?.status === "coming-soon" ? "Coming soon" : "No usable observations in this view"}</h3>
        <p>
          {coverage?.status === "coming-soon"
            ? "This metric is visible in the beta, but the necessary normalized data are not ready yet."
            : "Try a different metric or a different season range."}
        </p>
      </div>
    );
  }

  return (
    <div className={`chartCanvas ${showLegend ? "" : "noLegend"}`.trim()}>
      {showLegend ? <ChartLegend selectedClubIds={selectedClubIds} /> : null}
      <div className="chartPlot">
        <ResponsiveContainer width="100%" height="100%">
          {chartType === "line" ? (
            <LineChart data={chartData} margin={{ top: 12, right: 8, left: 0, bottom: 28 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(19, 34, 28, 0.12)" />
              <XAxis
                dataKey="season"
                angle={isVerySmallScreen ? -28 : -35}
                textAnchor="end"
                height={isVerySmallScreen ? 58 : 72}
                tick={{ fontSize: 12 }}
                interval={seasonTickInterval}
                minTickGap={isVerySmallScreen ? 18 : 8}
              />
              <YAxis
                reversed={metric.reverseAxis}
                tickFormatter={(value) => metric.axisTick(value, { displayCurrency })}
                tick={{ fontSize: 12 }}
              />
              <Tooltip
                content={<ChartTooltip displayCurrency={displayCurrency} metric={metric} valueBasis={valueBasis} />}
              />
              {selectedClubIds.flatMap((clubId) => renderLineSeries(clubId))}
            </LineChart>
          ) : (
            <BarChart data={chartData} margin={{ top: 12, right: 8, left: 0, bottom: 28 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(19, 34, 28, 0.12)" />
              <XAxis
                dataKey="season"
                angle={isVerySmallScreen ? -28 : -35}
                textAnchor="end"
                height={isVerySmallScreen ? 58 : 72}
                tick={{ fontSize: 12 }}
                interval={seasonTickInterval}
                minTickGap={isVerySmallScreen ? 18 : 8}
              />
              <YAxis
                reversed={metric.reverseAxis}
                tickFormatter={(value) => metric.axisTick(value, { displayCurrency })}
                tick={{ fontSize: 12 }}
              />
              <Tooltip
                content={<ChartTooltip displayCurrency={displayCurrency} metric={metric} valueBasis={valueBasis} />}
              />
              {selectedClubIds.map((clubId) => {
                const club = clubConfigById[clubId];
                return (
                  <Bar
                    key={clubId}
                    dataKey={clubId}
                    fill={club.visuals.chart.fill}
                    stroke={club.visuals.chart.stroke}
                    strokeWidth={club.visuals.chart.stroke === club.visuals.chart.fill ? 0 : 1.5}
                    radius={[8, 8, 0, 0]}
                    name={club.shortName}
                  />
                );
              })}
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
}
