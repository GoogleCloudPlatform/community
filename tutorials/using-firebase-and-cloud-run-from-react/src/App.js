/**
 * Copyright 2022 Google Inc. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import React from 'react';
import { onAuthStateChanged, signOut } from 'firebase/auth';
import { projectId, auth, signInWithGoogle } from './Firebase';

export default class App extends React.Component {
  constructor (props) {
    super(props);

    this.userAuthHandler = this.userAuthHandler.bind(this);
    this.handleGetMessage = this.handleGetMessage.bind(this);

    this.state = {
      loginUser: null,
      message: 'no message'
    };
  }

  userAuthHandler (user) {
    if (user) {
      // Login
      this.setState({ loginUser: user });
    } else {
      // Logout
      this.setState({
        loginUser: null,
        message: 'no message'
      });
    }
  }

  componentDidMount () {
    onAuthStateChanged(auth, this.userAuthHandler);
  }

  handleGetMessage () {
    const callBackend = async () => {
      const baseURL = 'https://' + projectId + '.web.app';
      const apiEndpoint = baseURL + '/hello-world-service/api/v1/hello';
      const user = auth.currentUser;
      const token = await user.getIdToken();
      const request = {
        method: 'POST',
        headers: {
          Authorization: 'Bearer ' + token,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: user.displayName
        })
      };
      /* global fetch */
      fetch(apiEndpoint, request)
        .then((res) => res.json())
        .then((data) => this.setState({ message: data.message }));
    };
    const waitMessage = new Promise(resolve => {
      this.setState({ message: 'Wait...' });
      resolve();
    });
    waitMessage.then(callBackend);
  }

  render () {
    const loginImageURL = process.env.PUBLIC_URL + '/btn_google_signin_light_normal_web.png';
    let element = null;

    if (this.state.loginUser) {
      const displayName = auth.currentUser.displayName;
      const photoURL = auth.currentUser.photoURL;
      element = (
        <div>
          <button onClick={() => signOut(auth)}>Logout</button>
          <h1>Welcome {displayName}!</h1>
          <img style={{ margin: '10px' }} alt='Profile icon' src={photoURL} />
          <button onClick={this.handleGetMessage}>Get message from the backend API</button>
          <p>message: {this.state.message}</p>
        </div>
      );
    } else {
      element = (
        <div>
          <input type='image' alt='Sign in with Google'
            onClick={signInWithGoogle} src={loginImageURL} />
        </div>
      );
    }

    return (
      <div className='App' style={{ margin: '10px' }}>{element}</div>
    );
  }
}
