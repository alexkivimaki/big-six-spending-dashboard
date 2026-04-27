import React, { useMemo, useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import { BarChart3, LineChart as LineChartIcon, TrendingUp, Info } from "lucide-react";

const seasons = [
  "2008/09", "2009/10", "2010/11", "2011/12", "2012/13", "2013/14",
  "2014/15", "2015/16", "2016/17", "2017/18", "2018/19", "2019/20",
  "2020/21", "2021/22", "2022/23", "2023/24", "2024/25", "2025/26",
];

const clubs = [
  "Manchester City",
  "Manchester United",
  "Chelsea",
  "Arsenal",
  "Liverpool",
  "Tottenham Hotspur",
];

const clubColors = {
  "Manchester City": "#6CABDD",
  "Manchester United": "#DA291C",
  Chelsea: "#034694",
  Arsenal: "#EF0107",
  Liverpool: "#C8102E",
  "Tottenham Hotspur": "#132257",
};

const metricOptions = [
  { key: "spending", label: "Gross transfer spend" },
  { key: "income", label: "Transfer income" },
  { key: "netSpend", label: "Net transfer spend" },
  { key: "wages", label: "Estimated wages" },
  { key: "rawPlayerCost", label: "Raw player-cost estimate" },
];

// Values are €m, rounded. Based on the Big Six spending table created in ChatGPT.
const rawData = [
  // Manchester City
  ["Manchester City", "2008/09", 157.4, 26.5, 130.9, 95.0],
  ["Manchester City", "2009/10", 147.3, 29.2, 118.1, 153.0],
  ["Manchester City", "2010/11", 183.6, 40.2, 143.5, 197.0],
  ["Manchester City", "2011/12", 91.1, 31.2, 59.9, 232.0],
  ["Manchester City", "2012/13", 62.0, 44.3, 17.7, 250.0],
  ["Manchester City", "2013/14", 115.5, 11.3, 104.2, 135.0],
  ["Manchester City", "2014/15", 102.8, 30.3, 72.5, 155.0],
  ["Manchester City", "2015/16", 208.5, 67.4, 141.0, 170.0],
  ["Manchester City", "2016/17", 216.3, 35.4, 180.9, 155.0],
  ["Manchester City", "2017/18", 317.5, 91.4, 226.2, 156.0],
  ["Manchester City", "2018/19", 78.6, 57.6, 21.0, 174.0],
  ["Manchester City", "2019/20", 169.8, 71.0, 98.8, 180.0],
  ["Manchester City", "2020/21", 173.4, 64.0, 109.4, 165.0],
  ["Manchester City", "2021/22", 138.9, 93.8, 45.1, 194.0],
  ["Manchester City", "2022/23", 155.0, 162.2, -7.2, 229.0],
  ["Manchester City", "2023/24", 259.6, 138.8, 120.8, 226.0],
  ["Manchester City", "2024/25", 243.0, 141.7, 101.3, 260.0],
  ["Manchester City", "2025/26", 301.8, 102.3, 199.5, 265.0],

  // Manchester United
  ["Manchester United", "2008/09", 45.3, 7.5, 37.8, 110.0],
  ["Manchester United", "2009/10", 27.2, 94.0, -66.8, 115.0],
  ["Manchester United", "2010/11", 29.3, 18.0, 11.3, 120.0],
  ["Manchester United", "2011/12", 62.8, 24.0, 38.8, 130.0],
  ["Manchester United", "2012/13", 76.0, 7.0, 69.0, 140.0],
  ["Manchester United", "2013/14", 77.1, 1.8, 75.3, 155.0],
  ["Manchester United", "2014/15", 195.4, 48.0, 147.4, 165.0],
  ["Manchester United", "2015/16", 156.0, 102.0, 54.0, 175.0],
  ["Manchester United", "2016/17", 185.0, 48.0, 137.0, 190.0],
  ["Manchester United", "2017/18", 198.4, 11.5, 186.9, 205.0],
  ["Manchester United", "2018/19", 82.7, 30.0, 52.7, 220.0],
  ["Manchester United", "2019/20", 214.8, 81.0, 133.8, 230.0],
  ["Manchester United", "2020/21", 83.8, 17.0, 66.8, 225.0],
  ["Manchester United", "2021/22", 140.0, 29.0, 111.0, 235.0],
  ["Manchester United", "2022/23", 243.3, 13.3, 230.0, 260.0],
  ["Manchester United", "2023/24", 202.3, 52.3, 150.0, 250.0],
  ["Manchester United", "2024/25", 214.5, 52.0, 162.5, 240.0],
  ["Manchester United", "2025/26", 246.7, 74.2, 172.5, 225.0],

  // Chelsea
  ["Chelsea", "2008/09", 30.5, 44.6, -14.1, 180.0],
  ["Chelsea", "2009/10", 27.0, 112.0, -85.0, 185.0],
  ["Chelsea", "2010/11", 121.0, 30.0, 91.0, 190.0],
  ["Chelsea", "2011/12", 101.0, 39.0, 62.0, 200.0],
  ["Chelsea", "2012/13", 123.0, 76.0, 47.0, 205.0],
  ["Chelsea", "2013/14", 132.0, 67.0, 65.0, 215.0],
  ["Chelsea", "2014/15", 127.0, 113.0, 14.0, 220.0],
  ["Chelsea", "2015/16", 93.0, 87.0, 6.0, 225.0],
  ["Chelsea", "2016/17", 133.0, 101.0, 32.0, 113.0],
  ["Chelsea", "2017/18", 260.0, 194.0, 66.0, 120.0],
  ["Chelsea", "2018/19", 208.0, 79.0, 129.0, 130.0],
  ["Chelsea", "2019/20", 45.0, 163.0, -118.0, 145.0],
  ["Chelsea", "2020/21", 247.0, 66.0, 181.0, 160.0],
  ["Chelsea", "2021/22", 118.0, 130.0, -12.0, 180.0],
  ["Chelsea", "2022/23", 611.0, 67.0, 544.0, 260.0],
  ["Chelsea", "2023/24", 467.0, 255.0, 212.0, 245.0],
  ["Chelsea", "2024/25", 291.0, 189.0, 102.0, 197.0],
  ["Chelsea", "2025/26", 339.2, 334.3, 4.9, 188.0],

  // Arsenal
  ["Arsenal", "2008/09", 40.2, 25.8, 14.4, 95.0],
  ["Arsenal", "2009/10", 12.0, 47.7, -35.7, 105.0],
  ["Arsenal", "2010/11", 23.0, 8.1, 14.9, 112.0],
  ["Arsenal", "2011/12", 65.5, 78.3, -12.8, 118.0],
  ["Arsenal", "2012/13", 56.0, 65.9, -9.9, 125.0],
  ["Arsenal", "2013/14", 49.3, 12.2, 37.1, 130.0],
  ["Arsenal", "2014/15", 119.0, 27.8, 91.2, 135.0],
  ["Arsenal", "2015/16", 26.5, 2.5, 24.0, 140.0],
  ["Arsenal", "2016/17", 113.0, 10.4, 102.7, 150.0],
  ["Arsenal", "2017/18", 152.9, 162.4, -9.6, 158.0],
  ["Arsenal", "2018/19", 80.2, 9.1, 71.1, 150.0],
  ["Arsenal", "2019/20", 160.8, 53.7, 107.2, 136.0],
  ["Arsenal", "2020/21", 86.0, 19.2, 66.9, 176.0],
  ["Arsenal", "2021/22", 167.4, 31.4, 136.0, 136.0],
  ["Arsenal", "2022/23", 186.0, 23.4, 162.6, 153.0],
  ["Arsenal", "2023/24", 235.0, 69.1, 165.9, 197.0],
  ["Arsenal", "2024/25", 107.6, 83.8, 23.8, 195.0],
  ["Arsenal", "2025/26", 294.6, 13.9, 280.7, 218.0],

  // Liverpool
  ["Liverpool", "2008/09", 73.5, 46.5, 27.0, 90.0],
  ["Liverpool", "2009/10", 43.0, 42.0, 1.0, 95.0],
  ["Liverpool", "2010/11", 98.0, 88.0, 10.0, 100.0],
  ["Liverpool", "2011/12", 67.0, 30.0, 37.0, 105.0],
  ["Liverpool", "2012/13", 63.0, 18.0, 45.0, 110.0],
  ["Liverpool", "2013/14", 57.0, 32.0, 25.0, 120.0],
  ["Liverpool", "2014/15", 151.0, 88.0, 63.0, 130.0],
  ["Liverpool", "2015/16", 126.0, 89.0, 37.0, 140.0],
  ["Liverpool", "2016/17", 79.9, 83.8, -3.9, 155.0],
  ["Liverpool", "2017/18", 173.0, 188.0, -15.0, 165.0],
  ["Liverpool", "2018/19", 182.0, 40.0, 142.0, 175.0],
  ["Liverpool", "2019/20", 10.4, 38.0, -27.6, 185.0],
  ["Liverpool", "2020/21", 84.0, 44.0, 40.0, 195.0],
  ["Liverpool", "2021/22", 87.0, 49.0, 38.0, 205.0],
  ["Liverpool", "2022/23", 137.0, 81.0, 56.0, 230.0],
  ["Liverpool", "2023/24", 172.0, 52.0, 120.0, 220.0],
  ["Liverpool", "2024/25", 42.0, 41.0, 1.0, 200.0],
  ["Liverpool", "2025/26", 481.4, 219.5, 261.9, 230.0],

  // Tottenham Hotspur
  ["Tottenham Hotspur", "2008/09", 144.0, 88.1, 55.9, 60.0],
  ["Tottenham Hotspur", "2009/10", 41.0, 21.0, 20.0, 65.0],
  ["Tottenham Hotspur", "2010/11", 31.0, 22.0, 9.0, 70.0],
  ["Tottenham Hotspur", "2011/12", 25.0, 46.0, -21.0, 75.0],
  ["Tottenham Hotspur", "2012/13", 70.0, 35.0, 35.0, 80.0],
  ["Tottenham Hotspur", "2013/14", 122.0, 109.0, 13.0, 85.0],
  ["Tottenham Hotspur", "2014/15", 49.0, 40.0, 9.0, 90.0],
  ["Tottenham Hotspur", "2015/16", 75.0, 56.0, 19.0, 100.0],
  ["Tottenham Hotspur", "2016/17", 83.0, 38.0, 45.0, 105.0],
  ["Tottenham Hotspur", "2017/18", 121.0, 107.0, 14.0, 115.0],
  ["Tottenham Hotspur", "2018/19", 0.0, 5.0, -5.0, 125.0],
  ["Tottenham Hotspur", "2019/20", 150.0, 60.0, 90.0, 135.0],
  ["Tottenham Hotspur", "2020/21", 110.0, 13.0, 97.0, 145.0],
  ["Tottenham Hotspur", "2021/22", 97.0, 34.0, 63.0, 155.0],
  ["Tottenham Hotspur", "2022/23", 170.0, 38.0, 132.0, 165.0],
  ["Tottenham Hotspur", "2023/24", 249.0, 136.0, 113.0, 175.0],
  ["Tottenham Hotspur", "2024/25", 148.0, 73.0, 75.0, 185.0],
  ["Tottenham Hotspur", "2025/26", 265.6, 82.7, 182.9, 190.0],
];

const data = rawData.map(([club, season, spending, income, netSpend, wages]) => ({
  club,
  season,
  spending,
  income,
  netSpend,
  wages,
  rawPlayerCost: Number((netSpend + wages).toFixed(1)),
}));

function formatMoney(value) {
  const sign = value < 0 ? "-" : "";
  const abs = Math.abs(value);
  if (abs >= 1000) return `${sign}€${(abs / 1000).toFixed(2)}bn`;
  return `${sign}€${abs.toFixed(0)}m`;
}

function TooltipContent({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="tooltip">
      <div className="tooltipTitle">{label}</div>
      {payload.map((item) => (
        <div key={item.name} className="tooltipRow">
          <span style={{ color: item.color }}>{item.name}</span>
          <strong>{formatMoney(item.value)}</strong>
        </div>
      ))}
    </div>
  );
}

export default function App() {
  const [selectedClubs, setSelectedClubs] = useState(["Manchester City", "Arsenal"]);
  const [metric, setMetric] = useState("rawPlayerCost");
  const [startIndex, setStartIndex] = useState(0);
  const [endIndex, setEndIndex] = useState(seasons.length - 1);
  const [chartType, setChartType] = useState("line");

  const selectedMetric = metricOptions.find((m) => m.key === metric);
  const selectedSeasons = seasons.slice(startIndex, endIndex + 1);

  const filtered = useMemo(() => {
    return data.filter((d) => selectedClubs.includes(d.club) && selectedSeasons.includes(d.season));
  }, [selectedClubs, selectedSeasons]);

  const chartData = useMemo(() => {
    return selectedSeasons.map((season) => {
      const row = { season };
      selectedClubs.forEach((club) => {
        const found = data.find((d) => d.club === club && d.season === season);
        row[club] = found ? found[metric] : null;
      });
      return row;
    });
  }, [selectedClubs, selectedSeasons, metric]);

  const totals = useMemo(() => {
    return selectedClubs
      .map((club) => {
        const rows = filtered.filter((d) => d.club === club);
        const sum = (key) => rows.reduce((acc, row) => acc + row[key], 0);
        return {
          club,
          spending: sum("spending"),
          income: sum("income"),
          netSpend: sum("netSpend"),
          wages: sum("wages"),
          rawPlayerCost: sum("rawPlayerCost"),
        };
      })
      .sort((a, b) => b[metric] - a[metric]);
  }, [selectedClubs, filtered, metric]);

  function toggleClub(club) {
    setSelectedClubs((previous) => {
      if (previous.includes(club)) {
        if (previous.length === 1) return previous;
        return previous.filter((c) => c !== club);
      }
      return [...previous, club];
    });
  }

  function updateStart(value) {
    const next = Number(value);
    setStartIndex(Math.min(next, endIndex));
  }

  function updateEnd(value) {
    const next = Number(value);
    setEndIndex(Math.max(next, startIndex));
  }

  return (
    <div className="page">
      <main className="shell">
        <header className="hero">
          <div>
            <div className="pill">
              <BarChart3 size={16} />
              Premier League Big Six, 2008/09–2025/26
            </div>
            <h1>Club spending dashboard</h1>
            <p>
              Compare transfer spending, transfer income, net spend, estimated wages and raw player-cost estimates by club and season.
              All values are rounded and shown in €m.
            </p>
          </div>

          <div className="heroButtons">
            <button onClick={() => setSelectedClubs(["Arsenal", "Manchester City"])}>Arsenal vs City</button>
            <button onClick={() => setSelectedClubs(clubs)}>Show Big Six</button>
          </div>
        </header>

        <section className="layout">
          <aside className="card controls">
            <div>
              <h2>Controls</h2>
              <p>Select clubs, metric and comparison period.</p>
            </div>

            <div className="controlGroup">
              <label className="label">Clubs</label>
              <div className="clubList">
                {clubs.map((club) => (
                  <label className="clubItem" key={club}>
                    <input
                      type="checkbox"
                      checked={selectedClubs.includes(club)}
                      onChange={() => toggleClub(club)}
                    />
                    <span className="dot" style={{ backgroundColor: clubColors[club] }} />
                    <span>{club}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="controlGroup">
              <label className="label" htmlFor="metric">Metric</label>
              <select id="metric" value={metric} onChange={(event) => setMetric(event.target.value)}>
                {metricOptions.map((option) => (
                  <option key={option.key} value={option.key}>{option.label}</option>
                ))}
              </select>
            </div>

            <div className="controlGroup">
              <div className="rangeHeader">
                <label className="label">Season range</label>
                <span>{seasons[startIndex]} – {seasons[endIndex]}</span>
              </div>
              <div className="rangeInputs">
                <div>
                  <small>Start</small>
                  <input type="range" min="0" max={seasons.length - 1} value={startIndex} onChange={(e) => updateStart(e.target.value)} />
                </div>
                <div>
                  <small>End</small>
                  <input type="range" min="0" max={seasons.length - 1} value={endIndex} onChange={(e) => updateEnd(e.target.value)} />
                </div>
              </div>
            </div>

            <div className="controlGroup">
              <label className="label">Chart type</label>
              <div className="buttonGrid">
                <button className={chartType === "line" ? "active" : ""} onClick={() => setChartType("line")}>
                  <LineChartIcon size={16} /> Line
                </button>
                <button className={chartType === "bar" ? "active" : ""} onClick={() => setChartType("bar")}>
                  <BarChart3 size={16} /> Bar
                </button>
              </div>
            </div>

            <div className="note">
              <Info size={16} />
              <span>
                Transfer values are based on the dataset assembled in the analysis. Wage figures are estimated player payrolls, so wage-based totals should be treated as directional rather than audited accounting figures.
              </span>
            </div>
          </aside>

          <section className="content">
            <div className="kpis">
              <div className="card kpi">
                <span>Selected period</span>
                <strong>{seasons[startIndex]}–{seasons[endIndex]}</strong>
              </div>
              <div className="card kpi">
                <span>Selected metric</span>
                <strong>{selectedMetric?.label}</strong>
              </div>
              <div className="card kpi">
                <span>Highest total</span>
                <strong><TrendingUp size={18} /> {totals[0]?.club}</strong>
                <em>{formatMoney(totals[0]?.[metric] || 0)}</em>
              </div>
            </div>

            <div className="card chartCard">
              <div className="sectionHeader">
                <div>
                  <h2>Yearly trend</h2>
                  <p>{selectedMetric?.label}, €m per season.</p>
                </div>
              </div>

              <div className="chartWrap">
                <ResponsiveContainer width="100%" height="100%">
                  {chartType === "line" ? (
                    <LineChart data={chartData} margin={{ top: 10, right: 22, left: 0, bottom: 28 }}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="season" angle={-35} textAnchor="end" height={68} tick={{ fontSize: 12 }} />
                      <YAxis tickFormatter={(v) => `€${v}m`} />
                      <Tooltip content={<TooltipContent />} />
                      <Legend />
                      {selectedClubs.map((club) => (
                        <Line
                          key={club}
                          type="monotone"
                          dataKey={club}
                          stroke={clubColors[club]}
                          strokeWidth={3}
                          dot={{ r: 3 }}
                          activeDot={{ r: 6 }}
                        />
                      ))}
                    </LineChart>
                  ) : (
                    <BarChart data={chartData} margin={{ top: 10, right: 22, left: 0, bottom: 28 }}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="season" angle={-35} textAnchor="end" height={68} tick={{ fontSize: 12 }} />
                      <YAxis tickFormatter={(v) => `€${v}m`} />
                      <Tooltip content={<TooltipContent />} />
                      <Legend />
                      {selectedClubs.map((club) => (
                        <Bar key={club} dataKey={club} fill={clubColors[club]} radius={[6, 6, 0, 0]} />
                      ))}
                    </BarChart>
                  )}
                </ResponsiveContainer>
              </div>
            </div>

            <div className="card tableCard">
              <h2>Period totals</h2>
              <div className="tableWrap">
                <table>
                  <thead>
                    <tr>
                      <th>Club</th>
                      <th>Gross spend</th>
                      <th>Income</th>
                      <th>Net spend</th>
                      <th>Estimated wages</th>
                      <th>Raw player-cost</th>
                    </tr>
                  </thead>
                  <tbody>
                    {totals.map((row) => (
                      <tr key={row.club}>
                        <td>
                          <span className="dot" style={{ backgroundColor: clubColors[row.club] }} />
                          <strong>{row.club}</strong>
                        </td>
                        <td>{formatMoney(row.spending)}</td>
                        <td>{formatMoney(row.income)}</td>
                        <td>{formatMoney(row.netSpend)}</td>
                        <td>{formatMoney(row.wages)}</td>
                        <td><strong>{formatMoney(row.rawPlayerCost)}</strong></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </section>
        </section>
      </main>
    </div>
  );
}
