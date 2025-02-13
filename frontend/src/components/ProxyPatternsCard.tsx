import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import React, { useState } from "react";
import { Button, Card, Form, Modal, Table } from "react-bootstrap";
import { PlusCircle } from "react-bootstrap-icons";
import { DefaultService, ProxyPatternRead } from "../client";
import {
  listProxyPatternsOptions,
  listProxyPatternsQueryKey,
} from "../client/@tanstack/react-query.gen";
import ProxyPatternRow from "./ProxyPatternRow";

const AddPatternModal: React.FC<{
  show: boolean;
  onHide: () => void;
  onAdd: (pattern: string) => void;
}> = ({ show, onHide, onAdd }) => {
  return (
    <Modal show={show} onHide={onHide}>
      <Modal.Header closeButton>
        <Modal.Title>Add Proxy Pattern</Modal.Title>
      </Modal.Header>
      <Form
        onSubmit={(e) => {
          e.preventDefault();
          const formData = new FormData(e.currentTarget);
          onAdd(formData.get("pattern") as string);
          onHide();
        }}
      >
        <Modal.Body>
          <Form.Group>
            <Form.Label>Pattern</Form.Label>
            <Form.Control
              type="text"
              name="pattern"
              placeholder="Enter a pattern to match stream titles (e.g. patriots)"
              required
            />
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={onHide}>
            Cancel
          </Button>
          <Button variant="primary" type="submit">
            Add Pattern
          </Button>
        </Modal.Footer>
      </Form>
    </Modal>
  );
};

const ProxyPatternsCard: React.FC = () => {
  const queryClient = useQueryClient();
  const [showAddModal, setShowAddModal] = useState(false);

  const { data: patterns } = useQuery(listProxyPatternsOptions());

  const createMutation = useMutation({
    mutationFn: async (pattern: string) => {
      const { data: newPattern } = await DefaultService.createProxyPattern({
        body: { pattern, enabled: true },
      });
      return newPattern;
    },
    onSuccess: (newPattern) => {
      queryClient.setQueryData<ProxyPatternRead[]>(
        listProxyPatternsQueryKey(),
        (old) => [...old, newPattern],
      );
    },
  });

  const updateMutation = useMutation({
    mutationFn: async (data: {
      id: number;
      pattern?: string;
      enabled?: boolean;
    }) => {
      const { id, ...body } = data;
      const { data: updatedPattern } = await DefaultService.updateProxyPattern({
        path: { pattern_id: id },
        body,
      });
      return updatedPattern;
    },
    onSuccess: (updatedPattern) => {
      queryClient.setQueryData<ProxyPatternRead[]>(
        listProxyPatternsQueryKey(),
        (old) =>
          old.map((p) => (p.id === updatedPattern.id ? updatedPattern : p)),
      );
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      await DefaultService.deleteProxyPattern({ path: { pattern_id: id } });
    },
    onSuccess: (_, id) => {
      queryClient.setQueryData<ProxyPatternRead[]>(
        listProxyPatternsQueryKey(),
        (old) => old.filter((p) => p.id !== id),
      );
    },
  });

  return (
    <Card className="stream-card mb-4">
      <Card.Header className="d-flex justify-content-between align-items-center">
        <h5 className="mb-0">Auto-Record Patterns</h5>
        <Button
          variant="primary"
          size="sm"
          className="add-stream-btn"
          onClick={() => setShowAddModal(true)}
        >
          <PlusCircle className="me-2" />
          Add Pattern
        </Button>
      </Card.Header>
      <Card.Body className="p-0">
        {patterns?.length ? (
          <div className="table-responsive">
            <Table hover className="mb-0 align-middle">
              <thead className="bg-light">
                <tr>
                  <th className="px-4 py-3">Pattern</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3" style={{ width: "120px" }}>
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {patterns.map((pattern) => (
                  <ProxyPatternRow
                    key={pattern.id}
                    pattern={pattern}
                    onUpdate={(data) =>
                      updateMutation.mutate({ id: pattern.id, ...data })
                    }
                    onDelete={() => deleteMutation.mutate(pattern.id)}
                  />
                ))}
              </tbody>
            </Table>
          </div>
        ) : (
          <div className="text-center text-muted py-4">
            No proxy patterns configured. Click "Add Pattern" to add one.
          </div>
        )}
      </Card.Body>

      <AddPatternModal
        show={showAddModal}
        onHide={() => setShowAddModal(false)}
        onAdd={(pattern) => createMutation.mutate(pattern)}
      />
    </Card>
  );
};

export default ProxyPatternsCard;
