import { useState } from "react";
import { LoginPage } from "./LoginPage";
import { RegisterPage } from "./RegisterPage";
import { DashboardPage } from "./DashboardPage";


export const Main = () => {


  const [currPage, setCurrPage] = useState<string>(() => {
    const SavedCurrPage = window.localStorage.getItem('currPage');
    return SavedCurrPage ? SavedCurrPage : "LoginPage";
    });

  const [username, setUsername] = useState<string>(() => {
    const SavedUsername = window.localStorage.getItem('username');
    return SavedUsername ? SavedUsername : '';
    });

  const loginCallback = (curr: string) => {
    setCurrPage(curr)
  }

  return (
    <div>
      {currPage === "LoginPage" ? (
        <LoginPage callback={loginCallback} />
      ) : (
        <></>
      )}
      {currPage === "RegisterPage" ? (<RegisterPage callback={loginCallback} />) : <></>}
      {currPage === "DashboardPage" ? (<DashboardPage callback={loginCallback} />) : <></>}
    </div>
  );
};
