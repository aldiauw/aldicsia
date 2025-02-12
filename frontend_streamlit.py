import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime

# Google Sheets Authorization
creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets.connections)
client = gspread.authorize(creds)

# Function to load data from Google Sheets
@st.cache_data(ttl=60)
def load_data(sheet_name):
    sheet = client.open("Inventory_Management").worksheet(sheet_name)
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# Function to write data back to Google Sheets
def update_sheet(sheet_name, data_frame):
    sheet = client.open("Inventory_Management").worksheet(sheet_name)
    # Clear existing data
    sheet.clear()
    # Update with new data
    sheet.update([data_frame.columns.values.tolist()] + data_frame.values.tolist())

# Load data from Google Sheets into a pandas DataFrame
sheet_name = "Sheet1"
if 'df' not in st.session_state:
    st.session_state.df = load_data(sheet_name)

# Sidebar for Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["View Inventory", "Add New Item", "Edit/Delete Item"])

# Function to display the inventory
def view_inventory():
    st.subheader("Current Inventory")
    st.dataframe(st.session_state.df)
    st.write("### Filter Inventory")
    category_filter = st.selectbox("Filter by Category", options=["All"] + list(st.session_state.df["Category"].unique()))
    status_filter = st.selectbox("Filter by Status", options=["All", "In Stock", "Out of Stock", "Damaged"])

    # Apply Filters
    filtered_df = st.session_state.df.copy()
    if category_filter != "All":
        filtered_df = filtered_df[filtered_df["Category"] == category_filter]
    if status_filter != "All":
        filtered_df = filtered_df[filtered_df["Status"] == status_filter]

    st.write("### Filtered Inventory")
    st.dataframe(filtered_df)

# Function to add a new item to the inventory
def add_new_item():
    st.subheader("Add New Item")
    new_item_id = st.number_input("Item ID", min_value=1000, value=int(st.session_state.df["Item ID"].max()) + 1, step=1)
    new_item_name = st.text_input("Item Name")
    new_category = st.selectbox("Category", options=st.session_state.df["Category"].unique())
    new_quantity = st.number_input("Quantity", min_value=0, value=0, step=1)
    new_price = st.number_input("Price", min_value=0.0, value=0.0, step=0.01)
    new_location = st.text_input("Location")
    new_supplier = st.text_input("Supplier")
    new_status = st.selectbox("Status", options=["In Stock", "Out of Stock", "Damaged"])
    new_last_updated = st.date_input("Last Updated", value=datetime.today())

    if st.button("Add Item"):
        # Append new item to the session_state dataframe
        new_data = pd.DataFrame({
            "Item ID": [new_item_id],
            "Item Name": [new_item_name],
            "Category": [new_category],
            "Quantity": [new_quantity],
            "Price": [new_price],
            "Location": [new_location],
            "Supplier": [new_supplier],
            "Status": [new_status],
            "Last Updated": [new_last_updated.strftime("%Y-%m-%d")]
        })
        st.session_state.df = pd.concat([st.session_state.df, new_data], ignore_index=True)
        update_sheet(sheet_name, st.session_state.df)  # Update Google Sheet
        st.success(f"Item '{new_item_name}' has been added successfully!")
        st.dataframe(st.session_state.df)

# Function to edit or delete an existing item
def edit_delete_item():
    st.subheader("Edit or Delete Item")
    item_id = st.number_input("Enter Item ID to edit or delete", min_value=int(st.session_state.df["Item ID"].min()), value=int(st.session_state.df["Item ID"].min()), step=1)

    if item_id in st.session_state.df["Item ID"].values:
        # Fetch the item data
        item_data = st.session_state.df[st.session_state.df["Item ID"] == item_id]
        item_name = st.text_input("Item Name", value=item_data["Item Name"].values[0])
        category = st.selectbox("Category", options=st.session_state.df["Category"].unique(), index=list(st.session_state.df["Category"].unique()).index(item_data["Category"].values[0]))
        quantity = st.number_input("Quantity", min_value=0, value=int(item_data["Quantity"].values[0]), step=1)
        price = st.number_input("Price", min_value=0.0, value=float(item_data["Price"].values[0]), step=0.01)
        location = st.text_input("Location", value=item_data["Location"].values[0])
        supplier = st.text_input("Supplier", value=item_data["Supplier"].values[0])
        status = st.selectbox("Status", options=["In Stock", "Out of Stock", "Damaged"], index=["In Stock", "Out of Stock", "Damaged"].index(item_data["Status"].values[0]))
        last_updated = st.date_input("Last Updated", value=datetime.strptime(item_data["Last Updated"].values[0], "%d-%m-%Y"))

        if st.button("Update Item"):
            # Update the item data in the session_state dataframe
            st.session_state.df.loc[st.session_state.df["Item ID"] == item_id, ["Item Name", "Category", "Quantity", "Price", "Location", "Supplier", "Status", "Last Updated"]] = [
                item_name, category, quantity, price, location, supplier, status, last_updated.strftime("%d-%m-%Y")
            ]
            update_sheet(sheet_name, st.session_state.df)  # Update Google Sheet
            st.success(f"Item ID {item_id} has been updated successfully!")
            st.dataframe(st.session_state.df)

        if st.button("Delete Item"):
            # Delete the item from the session_state dataframe
            st.session_state.df.drop(st.session_state.df[st.session_state.df["Item ID"] == item_id].index, inplace=True)
            update_sheet(sheet_name, st.session_state.df)  # Update Google Sheet
            st.success(f"Item ID {item_id} has been deleted successfully!")
            st.dataframe(st.session_state.df)
    else:
        st.error(f"No item found with ID {item_id}")

# Display the appropriate page based on user selection
if page == "View Inventory":
    view_inventory()
elif page == "Add New Item":
    add_new_item()
elif page == "Edit/Delete Item":
    edit_delete_item()
