import * as React from 'react';
import { useTheme } from '@mui/material/styles';
import { LineChart, Line, XAxis, YAxis, Label, ResponsiveContainer } from 'recharts';
import Title from './Title';

import { useState, useEffect } from 'react';

// Generate Sales Data
function createData(tim, amount) {
  return { tim, amount };
}
const data = [
  createData('00:00', 0),
  createData('03:00', 3),
  createData('06:00', 6),
  createData('09:00', 8),
  createData('12:00', 1.5),
  createData('15:00', 20),
  createData('18:00', 24),
  createData('21:00', 24),
  createData('24:00', undefined),
];

function formatTime(isoTimeString) {
  const date = new Date(isoTimeString);
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  const seconds = String(date.getSeconds()).padStart(2, '0');
  return `${hours}:${minutes}:${seconds}`;
}

export default function Chart() {
  const theme = useTheme();
  const [WindData,setWindData]=useState([])

  

  function fetchdata(){
    fetch("http://localhost:8000/seri/list/?LHWD=True")
      .then((res)=>res.json())
      .then(json=>{
        const datas=[];
        console.log(json);
        json.map(data=>{
         datas.push(createData(formatTime(data.Time),data.WindSpeed))
        });
        setWindData(datas);
      })
      .catch((error)=>console.log(error))
  }

  useEffect(()=>{
    const intervalID=setInterval(() => {
      fetchdata();
    }, 1000);
    return ()=>{
      clearInterval(intervalID);
    }
  },[fetchdata])

  return (
    <React.Fragment>
      <Title>Minutes</Title>
      <ResponsiveContainer>
        <LineChart
          data={WindData}
          margin={{
            top: 16,
            right: 16,
            bottom: 0,
            left: 24,
          }}
        >
          <XAxis
            dataKey="time"
            stroke={theme.palette.text.secondary}
            style={theme.typography.body2}
          />
          <YAxis
            stroke={theme.palette.text.secondary}
            style={theme.typography.body2}
          >
            <Label
              angle={270}
              position="left"
              style={{
                textAnchor: 'middle',
                fill: theme.palette.text.primary,
                ...theme.typography.body1,
              }}
            >
              Speed (m/s)
            </Label>
          </YAxis>
          <Line
            isAnimationActive={false}
            type="monotone"
            dataKey="amount"
            stroke={theme.palette.primary.main}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </React.Fragment>
  );
}
