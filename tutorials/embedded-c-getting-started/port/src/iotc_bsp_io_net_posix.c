/* Copyright 2018-2019 Google LLC
 *
 * This is part of the Google Cloud IoT Device SDK for Embedded C,
 * it is licensed under the BSD 3-Clause license; you may not use this file
 * except in compliance with the License.
 *
 * You may obtain a copy of the License at:
 *  https://opensource.org/licenses/BSD-3-Clause
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include <iotc_bsp_io_net.h>

#include <errno.h>
#include <fcntl.h>
#include <netdb.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <unistd.h>

#include <stdio.h>

#ifdef __cplusplus
extern "C" {
#endif

#ifndef MAX
#define MAX(a, b) (((a) > (b)) ? (a) : (b))
#endif

iotc_bsp_io_net_state_t iotc_bsp_io_net_create_socket(
    iotc_bsp_socket_t* iotc_socket) {
  *iotc_socket = socket(AF_INET, SOCK_STREAM, 0);

  if (-1 == *iotc_socket) {
    return IOTC_BSP_IO_NET_STATE_ERROR;
  }

  /* Enable nonblocking mode for a posix socket */
  const int flags = fcntl(*iotc_socket, F_GETFL, 0);

  if (-1 == flags || -1 == fcntl(*iotc_socket, F_SETFL, flags | O_NONBLOCK)) {
    return IOTC_BSP_IO_NET_STATE_ERROR;
  }

  return IOTC_BSP_IO_NET_STATE_OK;
}

iotc_bsp_io_net_state_t iotc_bsp_io_net_connect(iotc_bsp_socket_t* iotc_socket,
                                                const char* host,
                                                uint16_t port) {
  struct hostent* hostinfo = gethostbyname(host);

  /* if null it means that the address has not been found */
  if (NULL == hostinfo) {
    return IOTC_BSP_IO_NET_STATE_ERROR;
  }

  struct sockaddr_in name = {
      .sin_family = AF_INET,
      .sin_port = htons(port),
      .sin_addr = *((struct in_addr*)hostinfo->h_addr_list[0]),
      .sin_zero = {0}};

  if (-1 ==
      connect(*iotc_socket, (struct sockaddr*)&name, sizeof(struct sockaddr))) {
    return (EINPROGRESS == errno) ? IOTC_BSP_IO_NET_STATE_OK
                                  : IOTC_BSP_IO_NET_STATE_ERROR;
  } else {
    // todo_atigyi: what to do here?
    // does this mean the socket is BLOCKING?
    return IOTC_BSP_IO_NET_STATE_ERROR;
  }

  return IOTC_BSP_IO_NET_STATE_ERROR;
}

iotc_bsp_io_net_state_t iotc_bsp_io_net_connection_check(
    iotc_bsp_socket_t iotc_socket, const char* host, uint16_t port) {
  (void)host;
  (void)port;

  int valopt = 0;
  socklen_t lon = sizeof(int);

  if (getsockopt(iotc_socket, SOL_SOCKET, SO_ERROR, (void*)(&valopt), &lon) <
      0) {
    return IOTC_BSP_IO_NET_STATE_ERROR;
  }

  if (valopt) {
    return IOTC_BSP_IO_NET_STATE_ERROR;
  }

  return IOTC_BSP_IO_NET_STATE_OK;
}

iotc_bsp_io_net_state_t iotc_bsp_io_net_write(iotc_bsp_socket_t iotc_socket,
                                              int* out_written_count,
                                              const uint8_t* buf,
                                              size_t count) {
  if (NULL == out_written_count || NULL == buf) {
    return IOTC_BSP_IO_NET_STATE_ERROR;
  }

  int errval = 0;
  socklen_t lon = sizeof(int);

  if (getsockopt(iotc_socket, SOL_SOCKET, SO_ERROR, (void*)(&errval), &lon) <
      0) {
    errval = errno;
    errno = 0;
    return IOTC_BSP_IO_NET_STATE_ERROR;
  }

  if (errval != 0) {
    return IOTC_BSP_IO_NET_STATE_ERROR;
  }

  *out_written_count = write(iotc_socket, buf, count);

  if (*out_written_count < 0) {
    *out_written_count = 0;

    errval = errno;
    errno = 0;

    if (EAGAIN == errval) {
      return IOTC_BSP_IO_NET_STATE_BUSY;
    }

    if (ECONNRESET == errval || EPIPE == errval) {
      return IOTC_BSP_IO_NET_STATE_CONNECTION_RESET;
    }

    return IOTC_BSP_IO_NET_STATE_ERROR;
  }

  return IOTC_BSP_IO_NET_STATE_OK;
}

iotc_bsp_io_net_state_t iotc_bsp_io_net_read(iotc_bsp_socket_t iotc_socket,
                                             int* out_read_count, uint8_t* buf,
                                             size_t count) {
  if (NULL == out_read_count || NULL == buf) {
    return IOTC_BSP_IO_NET_STATE_ERROR;
  }

  int errval = 0;
  *out_read_count = read(iotc_socket, buf, count);

  if (*out_read_count < 0) {
    *out_read_count = 0;

    errval = errno;
    errno = 0;

    if (EAGAIN == errval) {
      return IOTC_BSP_IO_NET_STATE_BUSY;
    }

    if (ECONNRESET == errval || EPIPE == errval) {
      return IOTC_BSP_IO_NET_STATE_CONNECTION_RESET;
    }

    return IOTC_BSP_IO_NET_STATE_ERROR;
  }

  if (0 == *out_read_count) {
    return IOTC_BSP_IO_NET_STATE_CONNECTION_RESET;
  }

  return IOTC_BSP_IO_NET_STATE_OK;
}

iotc_bsp_io_net_state_t iotc_bsp_io_net_close_socket(
    iotc_bsp_socket_t* iotc_socket) {
  if (NULL == iotc_socket) {
    return IOTC_BSP_IO_NET_STATE_ERROR;
  }

  shutdown(*iotc_socket, SHUT_RDWR);

  close(*iotc_socket);

  *iotc_socket = 0;

  return IOTC_BSP_IO_NET_STATE_OK;
}

iotc_bsp_io_net_state_t iotc_bsp_io_net_select(
    iotc_bsp_socket_events_t* socket_events_array,
    size_t socket_events_array_size, long timeout_sec) {
  fd_set rfds;
  fd_set wfds;
  fd_set efds;

  FD_ZERO(&rfds);
  FD_ZERO(&wfds);
  FD_ZERO(&efds);

  int max_fd_read = 0;
  int max_fd_write = 0;
  int max_fd_error = 0;

  struct timeval tv = {0, 0};

  /* translate the library socket events settings to the event sets used by
   * posix select
   */
  size_t socket_id = 0;
  for (socket_id = 0; socket_id < socket_events_array_size; ++socket_id) {
    iotc_bsp_socket_events_t* socket_events = &socket_events_array[socket_id];

    if (NULL == socket_events) {
      return IOTC_BSP_IO_NET_STATE_ERROR;
    }

    if (1 == socket_events->in_socket_want_read) {
      FD_SET(socket_events->iotc_socket, &rfds);
      max_fd_read = socket_events->iotc_socket > max_fd_read
                        ? socket_events->iotc_socket
                        : max_fd_read;
    }

    if ((1 == socket_events->in_socket_want_write) ||
        (1 == socket_events->in_socket_want_connect)) {
      FD_SET(socket_events->iotc_socket, &wfds);
      max_fd_write = socket_events->iotc_socket > max_fd_write
                         ? socket_events->iotc_socket
                         : max_fd_write;
    }

    if (1 == socket_events->in_socket_want_error) {
      FD_SET(socket_events->iotc_socket, &efds);
      max_fd_error = socket_events->iotc_socket > max_fd_error
                         ? socket_events->iotc_socket
                         : max_fd_error;
    }
  }

  /* calculate max fd */
  const int max_fd = MAX(max_fd_read, MAX(max_fd_write, max_fd_error));

  tv.tv_sec = timeout_sec;

  /* call the actual posix select */
  const int result = select(max_fd + 1, &rfds, &wfds, &efds, &tv);

  if (0 < result) {
    /* translate the result back to the socket events structure */
    for (socket_id = 0; socket_id < socket_events_array_size; ++socket_id) {
      iotc_bsp_socket_events_t* socket_events = &socket_events_array[socket_id];

      if (FD_ISSET(socket_events->iotc_socket, &rfds)) {
        socket_events->out_socket_can_read = 1;
      }

      if (FD_ISSET(socket_events->iotc_socket, &wfds)) {
        if (1 == socket_events->in_socket_want_connect) {
          socket_events->out_socket_connect_finished = 1;
        }

        if (1 == socket_events->in_socket_want_write) {
          socket_events->out_socket_can_write = 1;
        }
      }

      if (FD_ISSET(socket_events->iotc_socket, &efds)) {
        socket_events->out_socket_error = 1;
      }
    }

    return IOTC_BSP_IO_NET_STATE_OK;
  } else if (0 == result) {
    return IOTC_BSP_IO_NET_STATE_TIMEOUT;
  }

  return IOTC_BSP_IO_NET_STATE_ERROR;
}

#ifdef __cplusplus
}
#endif
