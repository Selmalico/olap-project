import {
  LineChart, Line, Bar, PieChart, Pie, Cell,
  ComposedChart, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer
} from 'recharts';

interface Props {
  data: any[];
  config: any;
}

const COLORS = ["#2E75B6", "#00B0F0", "#1F7A4D", "#C55A11", "#5B2D8E", "#C00000"];

export function ChartPanel({ data, config }: Props) {
  if (!data || data.length === 0 || !config) return null;

  const commonProps = {
    data,
    margin: { top: 10, right: 20, left: 10, bottom: 5 }
  };

  const renderChart = () => {
    switch (config.chart_type) {
      case 'LineChart':
        return (
          <LineChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey={config.x_axis} tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            {config.show_legend && <Legend />}
            {(config.y_axes || []).map((ax: any, i: number) => (
              <Line key={ax.field} type="monotone" dataKey={ax.field}
                stroke={ax.color || COLORS[i]} strokeWidth={2} dot={false} />
            ))}
          </LineChart>
        );
      case 'PieChart':
        return (
          <PieChart>
            <Pie data={data} dataKey={(config.y_axes?.[0]?.field) || 'value'}
              nameKey={config.x_axis} cx="50%" cy="50%" outerRadius={120} label>
              {data.map((_: any, i: number) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            {config.show_legend && <Legend />}
          </PieChart>
        );
      default: // BarChart or ComposedChart
        return (
          <ComposedChart {...commonProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey={config.x_axis} tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            {config.show_legend && <Legend />}
            {(config.y_axes || []).map((ax: any, i: number) => (
              ax.type === 'line'
                ? <Line key={ax.field} type="monotone" dataKey={ax.field}
                    stroke={ax.color || COLORS[i]} strokeWidth={2} />
                : <Bar key={ax.field} dataKey={ax.field}
                    fill={ax.color || COLORS[i]} radius={[3, 3, 0, 0]} />
            ))}
          </ComposedChart>
        );
    }
  };

  return (
    <div className="mt-4 p-4 bg-white border border-gray-200 rounded-lg">
      {config.title && (
        <h3 className="text-sm font-semibold text-gray-700 mb-3">{config.title}</h3>
      )}
      <ResponsiveContainer width="100%" height={280}>
        {renderChart()}
      </ResponsiveContainer>
    </div>
  );
}
