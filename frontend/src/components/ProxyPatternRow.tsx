import React, { useState } from "react";
import { Button, Form } from "react-bootstrap";
import { Check, Pencil, Trash, X } from "react-bootstrap-icons";
import { ProxyPatternRead } from "../client/types.gen";

interface EditPatternFormData {
  pattern: string;
  enabled: boolean;
}

interface Props {
  pattern: ProxyPatternRead;
  onUpdate: (data: Partial<EditPatternFormData>) => void;
  onDelete: () => void;
}

const ProxyPatternRow: React.FC<Props> = ({ pattern, onUpdate, onDelete }) => {
  const [editing, setEditing] = useState(false);
  const [editData, setEditData] = useState<EditPatternFormData>({
    pattern: pattern.pattern,
    enabled: pattern.enabled,
  });

  if (editing) {
    return (
      <tr>
        <td className="px-4 py-3">
          <Form.Control
            size="sm"
            value={editData.pattern}
            onChange={(e) =>
              setEditData({
                ...editData,
                pattern: e.target.value,
              })
            }
          />
        </td>
        <td className="px-4 py-3">
          <Form.Check
            type="switch"
            checked={editData.enabled}
            onChange={(e) => {
              setEditData({
                ...editData,
                enabled: e.target.checked,
              });
              onUpdate({ enabled: e.target.checked });
            }}
            label="Enabled"
          />
        </td>
        <td className="px-4 py-3">
          <Button
            variant="link"
            className="me-2 p-1"
            onClick={() => {
              onUpdate(editData);
              setEditing(false);
            }}
          >
            <Check className="text-success" size={20} />
          </Button>
          <Button
            variant="link"
            className="p-1"
            onClick={() => setEditing(false)}
          >
            <X className="text-danger" size={20} />
          </Button>
        </td>
      </tr>
    );
  }

  return (
    <tr>
      <td className="px-4 py-3">{pattern.pattern}</td>
      <td className="px-4 py-3">
        <Form.Check
          type="switch"
          checked={pattern.enabled}
          onChange={(e) => onUpdate({ enabled: e.target.checked })}
          label="Enabled"
        />
      </td>
      <td className="px-4 py-3">
        <Button
          variant="link"
          className="me-2 p-1"
          onClick={() => setEditing(true)}
        >
          <Pencil size={20} />
        </Button>
        <Button variant="link" className="p-1" onClick={onDelete}>
          <Trash className="text-danger" size={20} />
        </Button>
      </td>
    </tr>
  );
};

export default ProxyPatternRow;
