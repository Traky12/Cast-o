import React, { useState, useEffect } from "react";
import Web3 from "web3";
import CropNFTABI from "./abis/CropNFT.json";
import MarketplaceABI from "./abis/CropNFTMarketplace.json";

const CROP_NFT_ADDRESS = process.env.REACT_APP_CROP_NFT_ADDRESS || "0x0000000000000000000000000000000000000000";
const MARKETPLACE_ADDRESS = process.env.REACT_APP_CROP_NFT_MARKETPLACE_ADDRESS || "0x0000000000000000000000000000000000000000";

function App() {
  const [web3, setWeb3] = useState(null);
  const [account, setAccount] = useState("");
  const [cropNFT, setCropNFT] = useState(null);
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
          setAccount(accounts[0] || "");

          if (CROP_NFT_ADDRESS !== "0x0000000000000000000000000000000000000000" &&
              MARKETPLACE_ADDRESS !== "0x0000000000000000000000000000000000000000") {
            const cropNFTContract = new web3Instance.eth.Contract(CropNFTABI, CROP_NFT_ADDRESS);
            const marketplaceContract = new web3Instance.eth.Contract(MarketplaceABI, MARKETPLACE_ADDRESS);
            setCropNFT(cropNFTContract);
            setMarketplace(marketplaceContract);

            const allListings = await marketplaceContract.methods.getAllListings().call();
            const normalized = allListings.map((l, i) => {
              const row = Array.isArray(l) ? { seller: l[0], tokenId: l[1], price: l[2], sold: l[3] } : l;
              return { listingId: i + 1, ...row };
            });
            setListings(normalized);
          }
        } catch (err) {
          console.error(err);
        }
      }
    };
    init();
  }, []);

  const createListing = async (tokenId, priceEth) => {
    if (!marketplace || !account || !web3) return;
    const priceWei = web3.utils.toWei(String(priceEth), "ether");
    await marketplace.methods.createListing(tokenId, priceWei).send({ from: account });
    const allListings = await marketplace.methods.getAllListings().call();
    const normalized = allListings.map((l, i) => {
      const row = Array.isArray(l) ? { seller: l[0], tokenId: l[1], price: l[2], sold: l[3] } : l;
      return { listingId: i + 1, ...row };
    });
    setListings(normalized);
  };

  const buyListing = async (listingId, priceWei) => {
    if (!marketplace || !account) return;
    await marketplace.methods.buyListing(listingId).send({ from: account, value: priceWei });
    const allListings = await marketplace.methods.getAllListings().call();
    const normalized = allListings.map((l, i) => {
      const row = Array.isArray(l) ? { seller: l[0], tokenId: l[1], price: l[2], sold: l[3] } : l;
      return { listingId: i + 1, ...row };
    });
    setListings(normalized);
  };

  return (
    <div style={{ padding: 20, fontFamily: "sans-serif" }}>
      <h1>CropNFT Marketplace</h1>
      <p>Account: {account || "Conectar wallet (MetaMask)"}</p>
      <div>
        <h2>Create Listing</h2>
        <input type="number" id="tokenId" placeholder="Token ID" />
        <input type="text" id="price" placeholder="Price (ETH)" />
        <button
          onClick={() =>
            createListing(
              Number(document.getElementById("tokenId").value),
              document.getElementById("price").value || "0"
            )
          }
        >
          Create Listing
        </button>
        <p style={{ fontSize: 12 }}>Aprobar el marketplace en CropNFT antes de listar (approve o setApprovalForAll).</p>
      </div>
      <div>
        <h2>Listings</h2>
        <ul style={{ listStyle: "none", padding: 0 }}>
          {listings.map((listing) => (
            <li key={listing.listingId} style={{ marginBottom: 12 }}>
              Listing #{listing.listingId} — Token ID: {String(listing.tokenId)} — Price: {web3 ? web3.utils.fromWei(String(listing.price), "ether") : listing.price} ETH
              {!listing.sold && listing.seller !== "0x0000000000000000000000000000000000000000" && (
                <button
                  style={{ marginLeft: 8 }}
                  onClick={() => buyListing(listing.listingId, String(listing.price))}
                >
                  Buy
                </button>
              )}
              {listing.sold && <span style={{ marginLeft: 8, color: "gray" }}>Sold</span>}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default App;
