/*
 * Copyright (c) 2017 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not
 * use this file except in compliance with the License. You may obtain a copy of
 * the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations under
 * the License.
 */

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using BookWebAPI.Models;
using Google.Cloud.Spanner.Data;
using Microsoft.AspNetCore.Mvc;

// For more information on enabling Web API for empty projects, visit https://go.microsoft.com/fwlink/?LinkID=397860

namespace BookWebAPI.Controllers
{
    [Route("api/[controller]/")]
    public class BookController : Controller
    {
        //TODO: Set your project id here
        private readonly string _myProject = "";


        [HttpGet]
        public async Task<IActionResult> GetAll()
        {
            var result = new List<Book>();

            using (var connection = new SpannerConnection(
                $"Data Source=projects/{_myProject}/instances/myspanner/databases/books"))
            {
                var selectCmd = connection.CreateSelectCommand("SELECT * FROM bookTable");
                using (var reader = await selectCmd.ExecuteReaderAsync())
                {
                    while (await reader.ReadAsync())
                        result.Add(new Book
                        {
                            Id = reader.GetFieldValue<string>("ID"),
                            Title = reader.GetFieldValue<string>("Title"),
                            Author = reader.GetFieldValue<string>("Author"),
                            PublishDate = reader.GetFieldValue<DateTime>("PublishDate")
                        });
                }
            }

            return Ok(result);
        }

        [HttpGet]
        [Route("{id}", Name = "GetBookById")]
        public async Task<IActionResult> Get(string id)
        {
            using (var connection = new SpannerConnection(
                $"Data Source=projects/{_myProject}/instances/myspanner/databases/books"))
            {
                var selectCommand = connection.CreateSelectCommand($"SELECT * FROM bookTable WHERE ID='{id}'");
                using (var reader = await selectCommand.ExecuteReaderAsync())
                {
                    while (await reader.ReadAsync())
                        return Ok(new Book
                        {
                            Id = reader.GetFieldValue<string>("ID"),
                            Title = reader.GetFieldValue<string>("Title"),
                            Author = reader.GetFieldValue<string>("Author"),
                            PublishDate = reader.GetFieldValue<DateTime>("PublishDate")
                        });
                }
            }

            return NotFound();
        }

        [HttpPost]
        public async Task<IActionResult> Create([FromBody] Book item)
        {
            // Insert a new item.
            using (var connection =
                new SpannerConnection(
                    $"Data Source=projects/{_myProject}/instances/myspanner/databases/books"))
            {
                await connection.OpenAsync();

                item.Id = Guid.NewGuid().ToString("N");
                var cmd = connection.CreateInsertCommand(
                    "bookTable", new SpannerParameterCollection
                    {
                        {"ID", SpannerDbType.String, item.Id},
                        {"Title", SpannerDbType.String, item.Title},
                        {"Author", SpannerDbType.String, item.Author},
                        {"PublishDate", SpannerDbType.Date, item.PublishDate}
                    });

                await cmd.ExecuteNonQueryAsync();
            }

            return CreatedAtRoute("GetBookById", new {id = item.Id}, item);
        }
    }
}
