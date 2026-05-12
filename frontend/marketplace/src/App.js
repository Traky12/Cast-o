import React, { useState, useEffect } from "react";
import Web3 from "web3";
import CarbonMarketplaceABI from "./CarbonMarketplaceABI.json";

const MARKETPLACE_ADDRESS = process.env.REACT_APP_MARKETPLACE_ADDRESS || "0x0000000000000000000000000000000000000000";

function App() {
  const [web3, setWeb3] = useState(null);
  const [account, setAccount] = useState("");
  const [marketplace, setMarketplace] = useState(null);
  const [listings, setListings] = useState([]);

  useEffect(() => {
    const init = async () => {
      if (window.ethereum) {
        const web3Instance = new Web3(window.ethereum);
        setWeb3(web3Instance);
        try {
          await window.ethereum.request({ method: "eth_requestAccounts" });
          const accounts = await web3Instance.eth.getAccounts();
          setAccount(accounts[0]);
          if (MARKETPLACE_ADDRESS !== "0x0000000000000000000000000000000000000000") {
            const contract = new web3Instance.eth.Contract(CarbonMarketplaceABI, MARKETPLACE_ADDRESS);
            setMarketplace(contract);
            const count = await contract.methods.listingCount().call();
            const all = [];
            for (let i = 1; i <= Number(count); i++) {
              const l = await contract.methods.getListing(i).call();
              all.push({ id: i, ...l });
            }
            setListings(all);
          }
        } catch (err) {
          console.error(err);
        }
      }
    };
    init();
  }, []);

  const createListing = async (kgCO2, pricePerKg) => {
    if (!marketplace || !account) return;
    await marketplace.methods.createListing(kgCO2, pricePerKg).send({ from: account });
    const count = await marketplace.methods.listingCount().call();
    const l = await marketplace.methods.getListing(count).call();
    setListings((prev) => [...prev, { id: Number(count), ...l }]);
  };

  const buyListing = async (listingId) => {
    if (!marketplace || !account) return;
    await marketplace.methods.buyListing(listingId).send({ from: account });
    const updated = await marketplace.methods.getListing(listingId).call();
    setListings((prev) => prev.map((l) => (l.id === listingId ? { ...l, sold: updated.sold } : l)));
  };

  return (
    <div style={{ padding: 20, fontFamily: "sans-serif" }}>
      <h1>Carbon Marketplace</h1>
      <p>Account: {account || "Conectar wallet"}</p>
      <div>
        <h2>Create Listing</h2>
        <input type="number" id="kgCO2" placeholder="kg CO₂" />
        <input type="number" id="pricePerKg" placeholder="Price per kg (BioCoin)" />
        <button
          onClick={() =>
            createListing(
              Number(document.getElementById("kgCO2").value),
              Number(document.getElementById("pricePerKg").value)
            )
          }
        >
          Create Listing
        </button>
      </div>
      <div>
        <h2>Listings</h2>
        <ul>
          {listings.map((listing) => (
            <li key={listing.id}>
              {listing.kgCO2} kg CO₂ - {listing.pricePerKgBioCoin} BioCoin/kg
              {!listing.sold && <button onClick={() => buyListing(listing.id)}>Buy</button>}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default App;
