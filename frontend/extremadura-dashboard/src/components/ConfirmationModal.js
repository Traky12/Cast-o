import React from "react";
import "./ConfirmationModal.css";

const ConfirmationModal = ({ isOpen, onClose, onConfirm, title, message }) => {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="confirmation-modal">
        <h3>{title}</h3>
        <div className="modal-body">{message}</div>
        <div className="modal-buttons">
          <button type="button" className="cancel-button" onClick={onClose}>
            Cancelar
          </button>
          <button
            type="button"
            className="confirm-button"
            onClick={onConfirm}
          >
            Confirmar
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmationModal;

