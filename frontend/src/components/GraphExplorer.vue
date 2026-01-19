<template>
  <div class="graph-explorer">
    <!-- Toolbar -->
    <div class="toolbar glass">
      <div class="toolbar-left">
        <button class="tool-btn" @click="fitToScreen" title="화면에 맞추기">
          <span>🔍</span> 맞추기
        </button>
        <button class="tool-btn" @click="refreshGraph" title="새로고침">
          <span>🔄</span> 새로고침
        </button>
        <div class="search-box">
          <input 
            v-model="searchQuery" 
            @keyup.enter="searchNodes"
            placeholder="노드 검색..." 
          />
          <button @click="searchNodes" class="search-btn">🔎</button>
        </div>
      </div>
      
      <div class="toolbar-right">
        <button class="tool-btn add-btn" @click="openAddNodeModal" title="노드 추가">
          <span>➕</span> 노드 추가
        </button>
        <button 
          class="tool-btn add-btn" 
          @click="startAddRelationship" 
          :class="{ active: isAddingRelationship }"
          title="관계 추가"
        >
          <span>🔗</span> 관계 추가
        </button>
        <span class="stats-badge" v-if="graphStats">
          {{ graphStats.nodes }} 노드 · {{ graphStats.relationships }} 관계
        </span>
      </div>
    </div>

    <!-- Graph Container -->
    <div class="graph-container" ref="graphContainer">
      <div class="loading-overlay" v-if="loading">
        <div class="spinner"></div>
        <p>그래프 로딩 중...</p>
      </div>
      
      <!-- Relationship Mode Hint -->
      <div class="relationship-hint glass" v-if="isAddingRelationship">
        <span>🔗</span>
        <p v-if="!relationshipSource">시작 노드를 클릭하세요</p>
        <p v-else>대상 노드를 클릭하세요 (ESC로 취소)</p>
        <button @click="cancelAddRelationship" class="cancel-btn">취소</button>
      </div>
    </div>

    <!-- Legend -->
    <div class="legend glass">
      <h4>범례</h4>
      <div class="legend-items">
        <div class="legend-item" v-for="label in uniqueLabels" :key="label">
          <span class="legend-dot" :style="{ background: getLabelColor(label) }"></span>
          <span>{{ label }}</span>
        </div>
      </div>
    </div>

    <!-- Node Detail Panel -->
    <transition name="slide">
      <div class="detail-panel glass" v-if="selectedNode">
        <div class="panel-header">
          <div class="node-labels">
            <span 
              v-for="label in selectedNode.labels" 
              :key="label" 
              class="label-badge"
              :style="{ background: getLabelColor(label) }"
            >
              {{ label }}
            </span>
          </div>
          <button class="close-btn" @click="closeDetailPanel">✕</button>
        </div>
        
        <div class="panel-content">
          <h3>{{ selectedNode.properties?.name || selectedNode.properties?.id || 'Node' }}</h3>
          
          <!-- Properties Editor -->
          <div class="properties-section">
            <div class="section-header">
              <h4>속성</h4>
              <button class="edit-toggle" @click="toggleEdit" v-if="!isEditing">
                ✏️ 편집
              </button>
              <div class="edit-actions" v-else>
                <button class="save-btn" @click="saveNodeChanges">💾 저장</button>
                <button class="cancel-edit-btn" @click="cancelEdit">취소</button>
              </div>
            </div>
            
            <div class="properties-grid" v-if="!isEditing">
              <template v-for="(value, key) in selectedNode.properties" :key="key">
                <div class="property-row" v-if="key !== 'embedding'">
                  <span class="property-key">{{ key }}</span>
                  <div class="property-value">
                    <span v-if="key === 'latex'" class="latex-value" v-html="renderLatex(value)"></span>
                    <span v-else-if="typeof value === 'object'">{{ JSON.stringify(value) }}</span>
                    <span v-else>{{ value }}</span>
                  </div>
                </div>
              </template>
            </div>
            
            <!-- Edit Mode -->
            <div class="properties-editor" v-else>
              <div 
                class="edit-row" 
                v-for="(value, key) in editableProperties" 
                :key="key"
              >
                <label>{{ key }}</label>
                <textarea 
                  v-if="key === 'latex' || key === 'description' || key === 'expression' || (typeof value === 'string' && value.length > 50)"
                  v-model="editableProperties[key]"
                  rows="3"
                ></textarea>
                <input 
                  v-else-if="typeof value === 'number'"
                  type="number"
                  v-model.number="editableProperties[key]"
                />
                <input 
                  v-else
                  type="text"
                  v-model="editableProperties[key]"
                />
              </div>
              
              <!-- Add new property -->
              <div class="add-property">
                <input v-model="newPropertyKey" placeholder="새 속성 이름" />
                <input v-model="newPropertyValue" placeholder="값" />
                <button @click="addNewProperty" :disabled="!newPropertyKey">➕</button>
              </div>
            </div>
          </div>
          
          <!-- Connections -->
          <div class="connections-section" v-if="selectedNode.connections?.length">
            <h4>연결된 노드</h4>
            <div class="connections-list">
              <div 
                class="connection-item"
                v-for="(conn, idx) in selectedNode.connections" 
                :key="idx"
                @click="focusNode(conn.connectedNode)"
              >
                <span class="connection-direction">
                  {{ conn.direction === 'outgoing' ? '→' : '←' }}
                </span>
                <span class="connection-type">{{ conn.relationship }}</span>
                <span class="connection-target">{{ conn.connectedCaption || 'Node' }}</span>
              </div>
            </div>
          </div>
          
          <!-- Actions -->
          <div class="panel-actions">
            <button class="action-btn danger" @click="confirmDeleteNode">
              🗑️ 노드 삭제
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- Add Node Modal -->
    <div class="modal-overlay" v-if="showAddNodeModal" @click.self="closeAddNodeModal">
      <div class="modal glass">
        <div class="modal-header">
          <h3>➕ 새 노드 추가</h3>
          <button class="close-btn" @click="closeAddNodeModal">✕</button>
        </div>
        
        <div class="modal-body">
          <div class="form-group">
            <label>레이블 (타입)</label>
            <select v-model="newNode.label">
              <option value="">선택하세요</option>
              <option v-for="label in availableLabels" :key="label" :value="label">
                {{ label }}
              </option>
              <option value="__custom__">직접 입력...</option>
            </select>
            <input 
              v-if="newNode.label === '__custom__'"
              v-model="newNode.customLabel"
              placeholder="새 레이블 이름"
              class="custom-label-input"
            />
          </div>
          
          <div class="form-group">
            <label>이름 (name)</label>
            <input v-model="newNode.name" placeholder="노드 이름" />
          </div>
          
          <div class="form-group" v-if="newNode.label === 'Formula' || newNode.customLabel === 'Formula'">
            <label>LaTeX 수식</label>
            <textarea v-model="newNode.latex" placeholder="예: P = \frac{I}{N} \cdot \frac{L}{B}" rows="3"></textarea>
          </div>
          
          <div class="form-group">
            <label>설명</label>
            <textarea v-model="newNode.description" placeholder="노드에 대한 설명" rows="3"></textarea>
          </div>
          
          <div class="form-group" v-if="newNode.label === 'Formula' || newNode.customLabel === 'Formula'">
            <label>Python 표현식</label>
            <input v-model="newNode.expression" placeholder="예: (I/N) * (L/B)" />
          </div>
        </div>
        
        <div class="modal-footer">
          <button class="btn secondary" @click="closeAddNodeModal">취소</button>
          <button class="btn primary" @click="createNewNode" :disabled="!isNewNodeValid">
            생성
          </button>
        </div>
      </div>
    </div>

    <!-- Add Relationship Modal -->
    <div class="modal-overlay" v-if="showRelationshipModal" @click.self="closeRelationshipModal">
      <div class="modal glass">
        <div class="modal-header">
          <h3>🔗 관계 추가</h3>
          <button class="close-btn" @click="closeRelationshipModal">✕</button>
        </div>
        
        <div class="modal-body">
          <div class="relationship-nodes">
            <div class="rel-node">
              <span class="rel-label">시작</span>
              <span class="rel-name">{{ relationshipSource?.caption }}</span>
            </div>
            <div class="rel-arrow">→</div>
            <div class="rel-node">
              <span class="rel-label">대상</span>
              <span class="rel-name">{{ relationshipTarget?.caption }}</span>
            </div>
          </div>
          
          <div class="form-group">
            <label>관계 유형</label>
            <select v-model="newRelationship.type">
              <option value="">선택하세요</option>
              <option v-for="type in availableRelTypes" :key="type" :value="type">
                {{ type }}
              </option>
              <option value="__custom__">직접 입력...</option>
            </select>
            <input 
              v-if="newRelationship.type === '__custom__'"
              v-model="newRelationship.customType"
              placeholder="새 관계 유형 (예: DEPENDS_ON)"
              class="custom-label-input"
            />
          </div>
        </div>
        
        <div class="modal-footer">
          <button class="btn secondary" @click="closeRelationshipModal">취소</button>
          <button class="btn primary" @click="createNewRelationship" :disabled="!isNewRelValid">
            생성
          </button>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div class="modal-overlay" v-if="showDeleteModal" @click.self="closeDeleteModal">
      <div class="modal glass small">
        <div class="modal-header">
          <h3>⚠️ 삭제 확인</h3>
        </div>
        <div class="modal-body">
          <p>
            <strong>{{ selectedNode?.properties?.name || 'Node' }}</strong>
            노드를 삭제하시겠습니까?
          </p>
          <p class="warning-text">연결된 모든 관계도 함께 삭제됩니다.</p>
        </div>
        <div class="modal-footer">
          <button class="btn secondary" @click="closeDeleteModal">취소</button>
          <button class="btn danger" @click="deleteNode">삭제</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue';
import axios from 'axios';
import katex from 'katex';
import cytoscape from 'cytoscape';

// Color palette for node labels
const LABEL_COLORS = {
  Formula: '#3b82f6',     // Blue
  Variable: '#10b981',    // Green
  Concept: '#f59e0b',     // Amber
  Definition: '#8b5cf6',  // Purple
  Section: '#ec4899',     // Pink
  Chapter: '#ef4444',     // Red
  Domain: '#06b6d4',      // Cyan
  Default: '#64748b'      // Gray
};

export default {
  name: 'GraphExplorer',
  
  setup() {
    const graphContainer = ref(null);
    const cyInstance = ref(null);
    
    const loading = ref(true);
    const searchQuery = ref('');
    const graphData = reactive({ nodes: [], relationships: [] });
    const selectedNode = ref(null);
    const isEditing = ref(false);
    const editableProperties = ref({});
    const newPropertyKey = ref('');
    const newPropertyValue = ref('');
    
    // Modal states
    const showAddNodeModal = ref(false);
    const showRelationshipModal = ref(false);
    const showDeleteModal = ref(false);
    
    // Relationship creation
    const isAddingRelationship = ref(false);
    const relationshipSource = ref(null);
    const relationshipTarget = ref(null);
    
    // Available labels and types
    const availableLabels = ref(['Formula', 'Variable', 'Concept', 'Definition', 'Domain']);
    const availableRelTypes = ref(['USES', 'USED_IN', 'DEFINES', 'RELATED_TO', 'PART_OF']);
    
    // New node form
    const newNode = reactive({
      label: '',
      customLabel: '',
      name: '',
      latex: '',
      description: '',
      expression: ''
    });
    
    // New relationship form
    const newRelationship = reactive({
      type: '',
      customType: ''
    });
    
    // Computed
    const graphStats = computed(() => {
      if (!graphData.nodes.length) return null;
      return {
        nodes: graphData.nodes.length,
        relationships: graphData.relationships.length
      };
    });
    
    const uniqueLabels = computed(() => {
      const labels = new Set();
      graphData.nodes.forEach(n => {
        if (n.labels) n.labels.forEach(l => labels.add(l));
      });
      return Array.from(labels);
    });
    
    const isNewNodeValid = computed(() => {
      const label = newNode.label === '__custom__' ? newNode.customLabel : newNode.label;
      return label && newNode.name;
    });
    
    const isNewRelValid = computed(() => {
      const type = newRelationship.type === '__custom__' ? newRelationship.customType : newRelationship.type;
      return type && relationshipSource.value && relationshipTarget.value;
    });
    
    // Methods
    const getLabelColor = (label) => {
      return LABEL_COLORS[label] || LABEL_COLORS.Default;
    };
    
    const loadGraphData = async () => {
      loading.value = true;
      try {
        const [dataRes, labelsRes, typesRes] = await Promise.all([
          axios.get('/api/graph/data?limit=300'),
          axios.get('/api/graph/labels'),
          axios.get('/api/graph/relationship-types')
        ]);
        
        graphData.nodes = dataRes.data.nodes;
        graphData.relationships = dataRes.data.relationships;
        availableLabels.value = labelsRes.data.labels;
        availableRelTypes.value = typesRes.data.types;
        
        await nextTick();
        initCytoscape();
      } catch (e) {
        console.error('Failed to load graph data:', e);
      } finally {
        loading.value = false;
      }
    };
    
    const initCytoscape = () => {
      if (!graphContainer.value || !graphData.nodes.length) return;
      
      // Clean up existing instance
      if (cyInstance.value) {
        cyInstance.value.destroy();
      }
      
      // Transform data for Cytoscape
      const elements = [];
      
      // Add nodes
      graphData.nodes.forEach(node => {
        elements.push({
          data: {
            id: node.id,
            label: node.caption || node.properties?.name || node.labels?.[0] || 'Node',
            nodeType: node.labels?.[0] || 'Default',
            color: getLabelColor(node.labels?.[0] || 'Default'),
            ...node
          }
        });
      });
      
      // Add edges
      graphData.relationships.forEach(rel => {
        elements.push({
          data: {
            id: rel.id,
            source: rel.source,
            target: rel.target,
            label: rel.type,
            ...rel
          }
        });
      });
      
      // Create Cytoscape instance
      cyInstance.value = cytoscape({
        container: graphContainer.value,
        elements: elements,
        style: [
          {
            selector: 'node',
            style: {
              'background-color': 'data(color)',
              'label': 'data(label)',
              'color': '#fff',
              'text-valign': 'bottom',
              'text-halign': 'center',
              'font-size': '11px',
              'text-margin-y': '8px',
              'width': '40px',
              'height': '40px',
              'border-width': '2px',
              'border-color': '#1e293b',
              'text-outline-width': '2px',
              'text-outline-color': '#0f172a',
              'text-wrap': 'ellipsis',
              'text-max-width': '80px'
            }
          },
          {
            selector: 'node:selected',
            style: {
              'border-width': '4px',
              'border-color': '#ffffff',
              'background-color': 'data(color)'
            }
          },
          {
            selector: 'node:active',
            style: {
              'overlay-opacity': 0.2
            }
          },
          {
            selector: 'edge',
            style: {
              'width': 2,
              'line-color': '#475569',
              'target-arrow-color': '#475569',
              'target-arrow-shape': 'triangle',
              'curve-style': 'bezier',
              'label': 'data(label)',
              'font-size': '9px',
              'color': '#94a3b8',
              'text-rotation': 'autorotate',
              'text-margin-y': '-10px',
              'text-outline-width': '1px',
              'text-outline-color': '#0f172a'
            }
          },
          {
            selector: 'edge:selected',
            style: {
              'line-color': '#3b82f6',
              'target-arrow-color': '#3b82f6',
              'width': 3
            }
          }
        ],
        layout: {
          name: 'cose',
          idealEdgeLength: 100,
          nodeOverlap: 20,
          refresh: 20,
          fit: true,
          padding: 30,
          randomize: false,
          componentSpacing: 100,
          nodeRepulsion: 400000,
          edgeElasticity: 100,
          nestingFactor: 5,
          gravity: 80,
          numIter: 1000,
          coolingFactor: 0.99,
          minTemp: 1.0
        },
        minZoom: 0.1,
        maxZoom: 3,
        wheelSensitivity: 0.3
      });
      
      // Event handlers
      cyInstance.value.on('tap', 'node', (evt) => {
        const node = evt.target;
        const nodeData = node.data();
        
        if (isAddingRelationship.value) {
          handleRelationshipNodeClick(nodeData);
        } else {
          selectNode(nodeData);
        }
      });
      
      cyInstance.value.on('tap', (evt) => {
        if (evt.target === cyInstance.value) {
          // Clicked on background
          if (!isAddingRelationship.value) {
            closeDetailPanel();
          }
        }
      });
      
      // Handle ESC key
      document.addEventListener('keydown', handleKeyDown);
    };
    
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        if (isAddingRelationship.value) {
          cancelAddRelationship();
        }
      }
    };
    
    const selectNode = async (nodeData) => {
      try {
        const res = await axios.get(`/api/graph/node/${nodeData.id}`);
        selectedNode.value = res.data;
        isEditing.value = false;
        
        // Highlight the selected node in Cytoscape
        if (cyInstance.value) {
          cyInstance.value.$(':selected').unselect();
          cyInstance.value.$(`#${CSS.escape(nodeData.id)}`).select();
        }
      } catch (e) {
        console.error('Failed to get node details:', e);
      }
    };
    
    const closeDetailPanel = () => {
      selectedNode.value = null;
      isEditing.value = false;
      if (cyInstance.value) {
        cyInstance.value.$(':selected').unselect();
      }
    };
    
    const toggleEdit = () => {
      if (!selectedNode.value) return;
      
      const props = { ...selectedNode.value.properties };
      delete props.embedding;
      editableProperties.value = props;
      isEditing.value = true;
    };
    
    const cancelEdit = () => {
      isEditing.value = false;
      editableProperties.value = {};
      newPropertyKey.value = '';
      newPropertyValue.value = '';
    };
    
    const addNewProperty = () => {
      if (!newPropertyKey.value) return;
      editableProperties.value[newPropertyKey.value] = newPropertyValue.value;
      newPropertyKey.value = '';
      newPropertyValue.value = '';
    };
    
    const saveNodeChanges = async () => {
      if (!selectedNode.value) return;
      
      try {
        const res = await axios.put(`/api/graph/node/${selectedNode.value.id}`, {
          properties: editableProperties.value
        });
        
        selectedNode.value.properties = res.data.properties;
        
        // Update graph visualization
        if (cyInstance.value) {
          const node = cyInstance.value.$(`#${CSS.escape(selectedNode.value.id)}`);
          node.data('label', res.data.properties.name || res.data.properties.id || 'Node');
        }
        
        isEditing.value = false;
      } catch (e) {
        console.error('Failed to save node:', e);
        alert('저장 실패: ' + e.message);
      }
    };
    
    const confirmDeleteNode = () => {
      showDeleteModal.value = true;
    };
    
    const closeDeleteModal = () => {
      showDeleteModal.value = false;
    };
    
    const deleteNode = async () => {
      if (!selectedNode.value) return;
      
      try {
        await axios.delete(`/api/graph/node/${selectedNode.value.id}`);
        
        // Remove from Cytoscape
        if (cyInstance.value) {
          cyInstance.value.$(`#${CSS.escape(selectedNode.value.id)}`).remove();
        }
        
        // Remove from local data
        graphData.nodes = graphData.nodes.filter(n => n.id !== selectedNode.value.id);
        graphData.relationships = graphData.relationships.filter(
          r => r.source !== selectedNode.value.id && r.target !== selectedNode.value.id
        );
        
        closeDeleteModal();
        closeDetailPanel();
      } catch (e) {
        console.error('Failed to delete node:', e);
        alert('삭제 실패: ' + e.message);
      }
    };
    
    const openAddNodeModal = () => {
      newNode.label = '';
      newNode.customLabel = '';
      newNode.name = '';
      newNode.latex = '';
      newNode.description = '';
      newNode.expression = '';
      showAddNodeModal.value = true;
    };
    
    const closeAddNodeModal = () => {
      showAddNodeModal.value = false;
    };
    
    const createNewNode = async () => {
      const label = newNode.label === '__custom__' ? newNode.customLabel : newNode.label;
      if (!label || !newNode.name) return;
      
      const properties = {
        name: newNode.name,
        id: `${label.toLowerCase()}_${Date.now()}`
      };
      
      if (newNode.description) properties.description = newNode.description;
      if (newNode.latex) properties.latex = newNode.latex;
      if (newNode.expression) properties.expression = newNode.expression;
      
      try {
        const res = await axios.post('/api/graph/node', { label, properties });
        
        // Add to Cytoscape
        if (cyInstance.value) {
          cyInstance.value.add({
            data: {
              id: res.data.id,
              label: res.data.properties.name,
              nodeType: label,
              color: getLabelColor(label),
              labels: res.data.labels,
              properties: res.data.properties
            },
            position: { x: 300, y: 300 }
          });
        }
        
        graphData.nodes.push({
          id: res.data.id,
          labels: res.data.labels,
          properties: res.data.properties,
          caption: res.data.properties.name
        });
        
        closeAddNodeModal();
      } catch (e) {
        console.error('Failed to create node:', e);
        alert('생성 실패: ' + e.message);
      }
    };
    
    const startAddRelationship = () => {
      isAddingRelationship.value = true;
      relationshipSource.value = null;
      relationshipTarget.value = null;
    };
    
    const cancelAddRelationship = () => {
      isAddingRelationship.value = false;
      relationshipSource.value = null;
      relationshipTarget.value = null;
    };
    
    const handleRelationshipNodeClick = (nodeData) => {
      if (!relationshipSource.value) {
        relationshipSource.value = {
          id: nodeData.id,
          caption: nodeData.label || nodeData.caption || 'Node'
        };
      } else if (nodeData.id !== relationshipSource.value.id) {
        relationshipTarget.value = {
          id: nodeData.id,
          caption: nodeData.label || nodeData.caption || 'Node'
        };
        showRelationshipModal.value = true;
        isAddingRelationship.value = false;
      }
    };
    
    const closeRelationshipModal = () => {
      showRelationshipModal.value = false;
      relationshipSource.value = null;
      relationshipTarget.value = null;
      newRelationship.type = '';
      newRelationship.customType = '';
    };
    
    const createNewRelationship = async () => {
      const type = newRelationship.type === '__custom__' ? newRelationship.customType : newRelationship.type;
      if (!type || !relationshipSource.value || !relationshipTarget.value) return;
      
      try {
        const res = await axios.post('/api/graph/relationship', {
          source_id: relationshipSource.value.id,
          target_id: relationshipTarget.value.id,
          type
        });
        
        // Add to Cytoscape
        if (cyInstance.value) {
          cyInstance.value.add({
            data: {
              id: res.data.id,
              source: res.data.source,
              target: res.data.target,
              label: res.data.type
            }
          });
        }
        
        graphData.relationships.push({
          id: res.data.id,
          source: res.data.source,
          target: res.data.target,
          type: res.data.type,
          properties: res.data.properties
        });
        
        closeRelationshipModal();
      } catch (e) {
        console.error('Failed to create relationship:', e);
        alert('관계 생성 실패: ' + e.message);
      }
    };
    
    const searchNodes = async () => {
      if (!searchQuery.value.trim()) {
        if (cyInstance.value) {
          cyInstance.value.fit();
        }
        return;
      }
      
      try {
        const res = await axios.get(`/api/graph/search?q=${encodeURIComponent(searchQuery.value)}`);
        
        if (res.data.nodes.length > 0 && cyInstance.value) {
          const firstNode = res.data.nodes[0];
          const cyNode = cyInstance.value.$(`#${CSS.escape(firstNode.id)}`);
          
          if (cyNode.length > 0) {
            cyInstance.value.animate({
              center: { eles: cyNode },
              zoom: 1.5
            }, { duration: 500 });
            
            selectNode({ id: firstNode.id, ...firstNode });
          }
        }
      } catch (e) {
        console.error('Search failed:', e);
      }
    };
    
    const focusNode = (nodeId) => {
      if (cyInstance.value) {
        const cyNode = cyInstance.value.$(`#${CSS.escape(nodeId)}`);
        if (cyNode.length > 0) {
          cyInstance.value.animate({
            center: { eles: cyNode },
            zoom: 1.5
          }, { duration: 500 });
          
          selectNode({ id: nodeId });
        }
      }
    };
    
    const fitToScreen = () => {
      if (cyInstance.value) {
        cyInstance.value.fit();
      }
    };
    
    const refreshGraph = () => {
      loadGraphData();
    };
    
    const renderLatex = (latex) => {
      if (!latex) return '';
      try {
        return katex.renderToString(latex, { displayMode: false, throwOnError: false });
      } catch (e) {
        return latex;
      }
    };
    
    // Lifecycle
    onMounted(() => {
      loadGraphData();
    });
    
    onUnmounted(() => {
      document.removeEventListener('keydown', handleKeyDown);
      if (cyInstance.value) {
        cyInstance.value.destroy();
      }
    });
    
    return {
      graphContainer,
      loading,
      searchQuery,
      graphData,
      graphStats,
      uniqueLabels,
      selectedNode,
      isEditing,
      editableProperties,
      newPropertyKey,
      newPropertyValue,
      showAddNodeModal,
      showRelationshipModal,
      showDeleteModal,
      isAddingRelationship,
      relationshipSource,
      relationshipTarget,
      availableLabels,
      availableRelTypes,
      newNode,
      newRelationship,
      isNewNodeValid,
      isNewRelValid,
      getLabelColor,
      loadGraphData,
      selectNode,
      closeDetailPanel,
      toggleEdit,
      cancelEdit,
      addNewProperty,
      saveNodeChanges,
      confirmDeleteNode,
      closeDeleteModal,
      deleteNode,
      openAddNodeModal,
      closeAddNodeModal,
      createNewNode,
      startAddRelationship,
      cancelAddRelationship,
      closeRelationshipModal,
      createNewRelationship,
      searchNodes,
      focusNode,
      fitToScreen,
      refreshGraph,
      renderLatex
    };
  }
};
</script>

<style scoped>
.graph-explorer {
  display: flex;
  flex-direction: column;
  height: 100%;
  position: relative;
  background: radial-gradient(ellipse at center, #1e293b 0%, #0f172a 100%);
}

/* Toolbar */
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  z-index: 10;
}

.toolbar-left, .toolbar-right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.tool-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: #e2e8f0;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
}

.tool-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: #3b82f6;
}

.tool-btn.active {
  background: rgba(59, 130, 246, 0.2);
  border-color: #3b82f6;
  color: #3b82f6;
}

.tool-btn.add-btn {
  background: rgba(16, 185, 129, 0.1);
  border-color: rgba(16, 185, 129, 0.3);
}

.tool-btn.add-btn:hover {
  background: rgba(16, 185, 129, 0.2);
  border-color: #10b981;
}

.search-box {
  display: flex;
  align-items: center;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  overflow: hidden;
}

.search-box input {
  background: transparent;
  border: none;
  padding: 0.5rem 0.75rem;
  color: #e2e8f0;
  font-size: 0.85rem;
  width: 200px;
  outline: none;
}

.search-box input::placeholder {
  color: #64748b;
}

.search-btn {
  background: transparent;
  border: none;
  padding: 0.5rem 0.75rem;
  cursor: pointer;
  font-size: 1rem;
}

.stats-badge {
  padding: 0.4rem 0.75rem;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 99px;
  color: #94a3b8;
  font-size: 0.75rem;
  font-family: 'JetBrains Mono', monospace;
}

/* Graph Container */
.graph-container {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.loading-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(15, 23, 42, 0.9);
  z-index: 100;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.relationship-hint {
  position: absolute;
  top: 1rem;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1.25rem;
  background: rgba(59, 130, 246, 0.15);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 12px;
  z-index: 50;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.relationship-hint .cancel-btn {
  background: rgba(239, 68, 68, 0.2);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 6px;
  padding: 0.25rem 0.75rem;
  color: #ef4444;
  font-size: 0.8rem;
  cursor: pointer;
}

/* Legend */
.legend {
  position: absolute;
  bottom: 1rem;
  left: 1rem;
  padding: 1rem;
  border-radius: 12px;
  background: rgba(20, 20, 30, 0.85);
  backdrop-filter: blur(10px);
  z-index: 20;
}

.legend h4 {
  font-size: 0.75rem;
  color: #64748b;
  margin-bottom: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.legend-items {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: #cbd5e1;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

/* Detail Panel */
.detail-panel {
  position: absolute;
  top: 0;
  right: 0;
  width: 380px;
  height: 100%;
  background: rgba(15, 23, 42, 0.95);
  backdrop-filter: blur(12px);
  border-left: 1px solid rgba(255, 255, 255, 0.08);
  overflow-y: auto;
  z-index: 30;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 1.25rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.node-labels {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.label-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 99px;
  font-size: 0.75rem;
  font-weight: 600;
  color: white;
}

.close-btn {
  background: rgba(255, 255, 255, 0.1);
  border: none;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.panel-content {
  padding: 1.25rem;
}

.panel-content h3 {
  font-size: 1.25rem;
  margin-bottom: 1.5rem;
  color: #f8fafc;
}

.properties-section {
  margin-bottom: 1.5rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.section-header h4 {
  font-size: 0.8rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.edit-toggle, .save-btn, .cancel-edit-btn {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  padding: 0.35rem 0.75rem;
  color: #94a3b8;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s;
}

.edit-toggle:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: #3b82f6;
  color: #3b82f6;
}

.edit-actions {
  display: flex;
  gap: 0.5rem;
}

.save-btn {
  background: rgba(16, 185, 129, 0.1);
  border-color: rgba(16, 185, 129, 0.3);
  color: #10b981;
}

.save-btn:hover {
  background: rgba(16, 185, 129, 0.2);
}

.properties-grid {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.property-row {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.75rem;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
}

.property-key {
  font-size: 0.7rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.property-value {
  font-size: 0.9rem;
  color: #e2e8f0;
  word-break: break-word;
}

.latex-value {
  font-size: 1rem;
}

/* Properties Editor */
.properties-editor {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.edit-row {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.edit-row label {
  font-size: 0.75rem;
  color: #64748b;
  text-transform: uppercase;
}

.edit-row input, .edit-row textarea {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  padding: 0.6rem 0.75rem;
  color: #e2e8f0;
  font-size: 0.9rem;
  font-family: inherit;
}

.edit-row input:focus, .edit-row textarea:focus {
  outline: none;
  border-color: #3b82f6;
}

.add-property {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.add-property input {
  flex: 1;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  padding: 0.5rem 0.75rem;
  color: #e2e8f0;
  font-size: 0.85rem;
}

.add-property button {
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.3);
  border-radius: 6px;
  padding: 0.5rem 0.75rem;
  color: #10b981;
  cursor: pointer;
}

.add-property button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Connections */
.connections-section {
  margin-bottom: 1.5rem;
}

.connections-section h4 {
  font-size: 0.8rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 0.75rem;
}

.connections-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.connection-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.connection-item:hover {
  background: rgba(59, 130, 246, 0.1);
}

.connection-direction {
  font-size: 1rem;
  color: #64748b;
}

.connection-type {
  font-size: 0.75rem;
  padding: 0.2rem 0.5rem;
  background: rgba(139, 92, 246, 0.2);
  color: #a78bfa;
  border-radius: 4px;
}

.connection-target {
  flex: 1;
  font-size: 0.85rem;
  color: #cbd5e1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Panel Actions */
.panel-actions {
  padding-top: 1rem;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.action-btn {
  width: 100%;
  padding: 0.75rem;
  border-radius: 8px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn.danger {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #ef4444;
}

.action-btn.danger:hover {
  background: rgba(239, 68, 68, 0.2);
}

/* Modals */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  width: 100%;
  max-width: 500px;
  background: rgba(20, 20, 30, 0.95);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  overflow: hidden;
}

.modal.small {
  max-width: 400px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.modal-header h3 {
  font-size: 1.1rem;
  color: #f8fafc;
}

.modal-body {
  padding: 1.5rem;
}

.modal-body p {
  color: #cbd5e1;
  margin-bottom: 0.5rem;
}

.warning-text {
  color: #f59e0b !important;
  font-size: 0.9rem;
}

.form-group {
  margin-bottom: 1.25rem;
}

.form-group label {
  display: block;
  font-size: 0.8rem;
  color: #94a3b8;
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.form-group input, .form-group textarea, .form-group select {
  width: 100%;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 0.75rem;
  color: #e2e8f0;
  font-size: 0.9rem;
  font-family: inherit;
}

.form-group select {
  cursor: pointer;
}

.form-group input:focus, .form-group textarea:focus, .form-group select:focus {
  outline: none;
  border-color: #3b82f6;
}

.custom-label-input {
  margin-top: 0.5rem;
}

.relationship-nodes {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 1rem;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 12px;
  margin-bottom: 1.5rem;
}

.rel-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
}

.rel-label {
  font-size: 0.7rem;
  color: #64748b;
  text-transform: uppercase;
}

.rel-name {
  font-size: 0.9rem;
  color: #e2e8f0;
  padding: 0.5rem 1rem;
  background: rgba(59, 130, 246, 0.1);
  border-radius: 8px;
}

.rel-arrow {
  font-size: 1.5rem;
  color: #3b82f6;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1.25rem;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.btn {
  padding: 0.6rem 1.25rem;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn.secondary {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #94a3b8;
}

.btn.secondary:hover {
  background: rgba(255, 255, 255, 0.1);
}

.btn.primary {
  background: #3b82f6;
  border: 1px solid #3b82f6;
  color: white;
}

.btn.primary:hover {
  background: #2563eb;
}

.btn.primary:disabled {
  background: #475569;
  border-color: #475569;
  cursor: not-allowed;
}

.btn.danger {
  background: #ef4444;
  border: 1px solid #ef4444;
  color: white;
}

.btn.danger:hover {
  background: #dc2626;
}

/* Transitions */
.slide-enter-active, .slide-leave-active {
  transition: transform 0.3s ease;
}

.slide-enter-from, .slide-leave-to {
  transform: translateX(100%);
}

/* Glass utility */
.glass {
  background: rgba(20, 20, 30, 0.7);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.08);
}
</style>
