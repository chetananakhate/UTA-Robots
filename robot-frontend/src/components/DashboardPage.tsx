import React, { useState, useEffect } from 'react';
import { Container, Grid, List, ListItem, ListItemText, Typography, Button, Paper, AppBar, Toolbar } from '@mui/material';

interface Device {
  id: string;
  name: string;
  os: string;
}

interface App {
  id: number;
  name: string;
  bot_runs: string[]; // Assuming run history is an array of strings
}

interface AvailableApp {
  id: number;
  name: string;
  dirictory_name: string;
  url: string;
  info_url: string;
}


export const DashboardPage = (props: {callback: (curr: string) => void}) => {
  
  const [selectedApp, setSelectedApp] = useState<App | null>(null);
  const [devices, setDevices] = useState<Device[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [installedApps, setApps] = useState<App[]>([]);
  const [availableApps, setAvailableApps] = useState<AvailableApp[]>([]);

  useEffect(() => {
    const getDevices = async () => {
      try {
        const username = window.localStorage.getItem('username');
        const response = await fetch(`http://127.0.0.1:5000/get_user_computers/${username}`);
        const jsonData = await response.json();
        setDevices(jsonData);
        console.log(jsonData);
      } catch (error) {
        console.error('Error fetching devices:', error);
      }
    };

    getDevices();
  }, []); 


  // const availableApps: App[] = [
  //   { id: 4, name: 'App 4', bot_runs: ['Run 1', 'Run 2', 'Run 3'] },
  //   { id: 5, name: 'App 5', bot_runs: ['Run 1', 'Run 2', 'Run 3'] },
  //   { id: 6, name: 'App 6', bot_runs: ['Run 1', 'Run 2', 'Run 3'] },
  // ];

  const getApps = async (device: Device) => {
    try {
      if (device) {
        // const device = device.id;
        const response = await fetch(`http://127.0.0.1:5000/get_computer_bots/${device.id}`);
        const jsonData = await response.json();
        console.log(jsonData);
        // const apps = await getApps(); // Wait for the apps data to be fetched
        setApps(jsonData);
        return jsonData; // Return the apps data
      }
      return []; // Return an empty array if no device is selected
    } catch (error) {
      console.error('Error fetching apps:', error);
      return []; // Return an empty array in case of error
    }
  };

  

  const getAvailableApps = async (device: Device) => {
    try {
      if (device) {
        // const device = device.id;
        const username = window.localStorage.getItem('username');
        const response = await fetch(`http://127.0.0.1:5000/get_available_bots/${username}/${device.id}`);
        const jsonData = await response.json();
        console.log(jsonData);
        // const apps = await getApps(); // Wait for the apps data to be fetched
        setAvailableApps(jsonData);
        return jsonData; // Return the apps data
      }
      return []; // Return an empty array if no device is selected
    } catch (error) {
      console.error('Error fetching apps:', error);
      return []; // Return an empty array in case of error
    }
  };

  const handleDeviceSelect = async (device: Device) => {
    setSelectedDevice(device);
    getApps(device);
    getAvailableApps(device);
    // const apps = await getApps(); // Wait for the apps data to be fetched
    // setApps(apps);
    setSelectedApp(null); // Reset selected app when changing devices
  };
  

  

  const handleAppSelect = (app: App) => {
    setSelectedApp(app);
  };

  // const handleAppInstall = async (app: AvailableApp) => {
  //   console.log(`Installing app ${app.name} on device ${selectedDevice?.name}`);
  //   try {
  //     if (app) {
  //       // const device = device.id;
  //       const username = window.localStorage.getItem('username');
  //       const response = fetch(`http://127.0.0.1:5000/trigger_bot_download/${selectedDevice?.id}/${app.id}`);
  //       const jsonData = (await response).json();
  //       console.log(jsonData);
  //       return jsonData; // Return the apps data
  //     }
  //     return []; // Return an empty array if no device is selected
  //   } catch (error) {
  //     console.error('Error requesting download bot:', error);
  //   }
  // };

  const handleAppInstall = async (app: AvailableApp) => {
    // const [isLoading, setLoading] = useState(false);
  
    // const handleButtonClick = async () => {
    //   setLoading(true);
  
      try {
        const username = window.localStorage.getItem('username');
        const response = await fetch(`http://127.0.0.1:5000/trigger_bot_download/${username}/${selectedDevice?.id}/${app.id}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            // Add any other headers as needed
          },
          body: JSON.stringify({
            user_id: username,
            computer_id: selectedDevice?.id,
            bot_id: app.id,
          }),
        });
  
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
  
        const data = await response.json();
        console.log('Success:', data);
        // Handle the response data as needed
  
      } catch (error) {
        console.error('Error:', error);
        // Handle errors
      } finally {
        // setLoading(false);
      }
    };

    const handleAppExecute = async (app: App) => {
    
        try {
          const username = window.localStorage.getItem('username');
          const response = await fetch(`http://127.0.0.1:5000/trigger_execute/${username}/${selectedDevice?.id}/${app.id}`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              // Add any other headers as needed
            },
            body: JSON.stringify({
              user_id: username,
              computer_id: selectedDevice?.id,
              bot_id: app.id,
            }),
          });
    
          if (!response.ok) {
            throw new Error('Network response was not ok');
          }
    
          const data = await response.json();
          console.log('Success:', data);
          // Handle the response data as needed
    
        } catch (error) {
          console.error('Error:', error);
          // Handle errors
        } finally {
          // setLoading(false);
        }
      };
  
  //   return (
  //     <div>
  //       <button onClick={handleButtonClick} disabled={isLoading}>
  //         {isLoading ? 'Loading...' : 'Trigger Bot Download'}
  //       </button>
  //     </div>
  //   );
  // };

  function handleSignOut(): void {

    window.localStorage.clear();
    props.callback("LoginPage")
    // throw new Error('Function not implemented.');
  }

  function handleAppDownload(): void {
    throw new Error('Function not implemented.');
  }

  return (
    <Container>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            App Name
          </Typography>
          <Button variant="contained" color="primary" onClick={() => handleSignOut()}>Sign out</Button>
        </Toolbar>
      </AppBar>

      <Grid container spacing={3}>
        <Grid item xs={3}>
        {devices[0] && (
          <Paper>
          <br />
            <Typography variant="h5" align="center" gutterBottom >Devices</Typography>
            <List>
              {devices.map((device: Device) => (
                <ListItem key={device.id} button onClick={() => handleDeviceSelect(device)} selected={selectedDevice?.id === device.id}>
                  <ListItemText primary={device.name} />
                </ListItem>
              ))}
            </List>
          </Paper>)}
        </Grid>

        <Grid item xs={6}>
          {selectedDevice ? (
            <Paper>
              <br />
              <Typography variant="h5" align="center" gutterBottom>Installed Apps</Typography>
              <List>
                {installedApps.map(app => (
                  <ListItem key={app.id} button onClick={() => handleAppSelect(app)} selected={selectedApp?.id === app.id}>
                    <ListItemText primary={app.name} />
                    <Button variant="contained" color="primary" onClick={() => handleAppExecute(app)}>Execute</Button>
                  </ListItem>
                ))}
              </List>
            </Paper>
          ) : (
            
            <Paper>
            <br />
            <Typography variant="body1" align="center">To make a new device available, Install the app on your computer.</Typography>
            <br />
            <Button variant="contained" color="primary" onClick={() => handleAppDownload()}>Download App</Button>
            <br />
            <br />
            </Paper>
          )}
        </Grid>

        <Grid item xs={3}>
          {selectedDevice && (
            <Paper>
              <br />
              <Typography variant="h5" align="center" gutterBottom>Available Apps to Install</Typography>
              <List>
                {availableApps.map(app => (
                  <ListItem button key={app.id}>
                    <ListItemText primary={app.name} />
                    <Button variant="contained" color="primary" onClick={() => handleAppInstall(app)}>Install</Button>
                  </ListItem>
                ))}
              </List>
            </Paper>
          )}
        </Grid>
      </Grid>

      {/* {selectedApp && (
        <Paper>
          <Typography variant="h5" align="center" gutterBottom>{selectedApp.name} Run History</Typography>
          <List>
            {selectedApp.bot_runs.map((run, index) => (
              <ListItem key={index}>
                <ListItemText primary={run} />
              </ListItem>
            ))}
          </List>
        </Paper>
      )} */}
    </Container>
  );
};
