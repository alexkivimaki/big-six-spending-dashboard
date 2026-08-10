export function SeasonHistoryTable({ rows }) {
  return (
    <div className="tableWrap">
      <table>
        <thead>
          <tr>
            <th>Season</th>
            <th>Gross spend</th>
            <th>Income</th>
            <th>Net spend</th>
            <th>Revenue</th>
            <th>Staff costs</th>
            <th>Staff / revenue</th>
            <th>Profit before tax</th>
            <th>Points</th>
            <th>League position</th>
            <th>Trophies</th>
            <th>Manager</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.season}>
              <td>{row.season}</td>
              <td>{row.grossSpend}</td>
              <td>{row.income}</td>
              <td>{row.netSpend}</td>
              <td>{row.revenue}</td>
              <td>{row.staffCosts}</td>
              <td>{row.staffRatio}</td>
              <td>{row.profitBeforeTax}</td>
              <td>{row.points}</td>
              <td>{row.leaguePosition}</td>
              <td>{row.trophies}</td>
              <td>{row.manager}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
