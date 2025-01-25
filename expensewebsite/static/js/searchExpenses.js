const searchField = document.querySelector("#searchField");
const appTable = document.querySelector(".app-table");
const tableOutput = document.querySelector(".table-output");
tableOutput.style.display = "none";
const paginationCotainer = document.querySelector(".pagination-container");
const tbody = document.querySelector(".table-body");

searchField.addEventListener("keyup", (e) => {
  const searchValue = e.target.value;

  if (searchValue.trim().length > 0) {
    console.log("searchValue", searchValue);
    paginationCotainer.style.display = "none";
    tbody.innerHTML = "";
    fetch("/search-expenses", {
      body: JSON.stringify({ searchText: searchValue }),
      method: "POST",
    })
      .then((res) => res.json())
      .then((data) => {
        console.log("Data: ", data);
        appTable.style.display = "none";
        tableOutput.style.display = "block";

        if (data.length === 0) {
          tableOutput.innerHTML = "No results found!";
        } else {
          data.forEach((item) => {
            tbody.innerHTML += `
            <tr>
            <td>${item.amount}</td>
            <td>${item.category}</td>
            <td>${item.description}</td>
            <td>${item.date}</td>
            <td>
                <a href="/edit-expense/${item.id}/" class="btn btn-secondary btn-sm">Edit</a>
            </td>
            </tr>
            `;
          });
        }
      });
  } else {
    tableOutput.style.display = "none";
    appTable.style.display = "block";
    paginationCotainer.style.display = "block";
  }
});
