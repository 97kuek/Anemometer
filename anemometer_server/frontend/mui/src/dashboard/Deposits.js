import * as React from 'react';
import Link from '@mui/material/Link';
import Typography from '@mui/material/Typography';
import Title from './Title';
import { Button } from '@mui/material';

import { useEffect, useState } from 'react';

function preventDefault(event) {
  event.preventDefault();
}

export default function Deposits() {
  const [WindSpeed,setWindSpeed]=useState();
  const [WindDirection,setWindDirection]=useState();
  const [UpdateTime,setUpdateTime]=useState();

  function formatTime(isoTimeString) {
    const date = new Date(isoTimeString);
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    return `${hours}:${minutes}:${seconds}`;
  }

  const fetchdata = () =>{
  fetch("http://localhost:8000/seri/list/?LD=True")
    .then((res)=>res.json())
    .then(json => {
      //console.log(json); // WindSpeedを変数windSpeedに代入
     // console.log("windspeed:",json[0].WindSpeed);
     // console.log("id",json[0].id);
      if (json.length != 0){
      setWindSpeed(json[0].WindSpeed);
      setWindDirection("--")
      setUpdateTime(formatTime(json[0].Time));
      }else{
        setWindSpeed("--");
        setWindDirection("--");
        setUpdateTime("--");
      }
    })
    .catch((error)=>console.log(error));
  }
  
  useEffect(()=>{
    fetchdata();
    const intervalID=setInterval(fetchdata,1000);

    return ()=>{
      clearInterval(intervalID);
    }
  })

  return (
    <React.Fragment>
      <Title>Current Speed</Title>
      <Typography component="p" variant="h4">
        {WindSpeed} m/s
      </Typography>
      <Typography component="p"variant='h4'>
        {WindDirection}
      </Typography>
      <Typography color="text.secondary" sx={{ flex: 1 }}>
        on {UpdateTime}
      </Typography>
      <div>
        <Button variant='contained' onClick={fetchdata} >Reload</Button>
      </div>
    </React.Fragment>
  );
}